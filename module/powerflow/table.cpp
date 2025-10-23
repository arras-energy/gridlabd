// module/powerflow/table.cpp

#include <fstream>
#include "gridlabd.h"
#include "powerflow.h"

cell::cell(const char *str, bool as_string)
{
    if ( ! as_string )
    {
        // void
        if ( str[0] == '\0' )
        {
            type = DT_VOID;
            return;
        }

        // bool
        if ( stricmp(str,"true") == 0 )
        {
            type = DT_BOOL;
            value.boolean = true;
            return;
        }
        if ( stricmp(str,"false") == 0 )
        {
            type = DT_BOOL;
            value.boolean = false;
            return;
        }
        
        // int
        char *end;
        value.integer = strtol(str,&end,10);
        if ( *end == '\0' )
        {
            type = DT_INT;
            return;
        }

        // float
        value.real = strtod(str,&end);
        if ( *end == '\0' )
        {
            type = DT_DOUBLE;
            return;
        }
    }

    type = DT_STRING;
    value.string = strdup(str);
}

cell::cell(void)
{
    type = DT_VOID;
}

cell::cell(bool boolean)
{
    type = DT_BOOL;
    value.boolean = boolean;
}

cell::cell(long long integer)
{
    type = DT_INT;
    value.integer = integer;
}

cell::cell(double real)
{
    type = DT_DOUBLE;
    value.real = real;
}

cell::~cell(void)
{
}

bool cell::to_bool(bool if_void)
{
    switch ( type )
    {
    case DT_VOID:
        return if_void;
    case DT_BOOL:
        return value.boolean;
    case DT_INT:
        return value.integer != 0;
    case DT_DOUBLE:
        return value.real != 0.0;
    case DT_STRING:
        return stricmp(value.string,"true") || atof(value.string) != 0.0;
    default:
        throw "cell::to_int() -- invalid data type";
    }
}

long long cell::to_int(long long if_void)
{
    switch ( type )
    {
    case DT_VOID:
        return if_void;
    case DT_BOOL:
        return value.boolean ? 1 : 0;
    case DT_INT:
        return value.integer;
    case DT_DOUBLE:
        return (long long)value.real;
    case DT_STRING:
        return atoll(value.string);
    default:
        throw "cell::to_int() -- invalid data type";
    }
}

double cell::to_double(double if_void)
{
    switch ( type )
    {
    case DT_VOID:
        return if_void;
    case DT_BOOL:
        return value.boolean ? 1.0 : 0.0;
    case DT_INT:
        return (double)value.integer;
    case DT_DOUBLE:
        return value.real;
    case DT_STRING:
        return atof(value.string);
    default:
        throw "cell::to_double() -- invalid data type";
    }
}

std::string cell::to_string(const char *if_void)
{
    char buffer[1024];
    switch ( type )
    {
    case DT_VOID:
        return std::string(if_void);
    case DT_BOOL:
        return std::string(value.boolean ? "TRUE" : "FALSE");
    case DT_INT:
        snprintf(buffer,sizeof(buffer)-1,"%lld",value.integer);
        return std::string(buffer);
    case DT_DOUBLE:
        snprintf(buffer,sizeof(buffer)-1,"%lg",value.real);
        return std::string(buffer);
    case DT_STRING:
        break;
    default:
        throw "cell::to_string() -- invalid data type";
    }
    return std::string(value.string);
}

table::table(const char *filename, bool as_string)
{
    // locate the file
    char pathname[1024];
    if ( gl_findfile(filename,NULL,R_OK,pathname,sizeof(pathname)-1) == NULL )
    {
        gl_error("unable to find '%s'",(const char*)filename);
        return;
    }

    // get the size of the file's contents
    struct stat buf;
    if ( stat(pathname,&buf) == -1 )
    {
        gl_error("unable to get size of '%s'",(const char*)pathname);       
        return;
    }

    // open file
    std::ifstream file(pathname);
    if ( ! file.is_open() )
    {
        gl_error("unable to open '%s'",pathname);
        return;
    }

    // read header
    ncolumns = 0;
    std::string line;
    if ( std::getline(file,line) )
    {
        char buffer[line.length()+1]; strcpy(buffer,line.c_str());
        char *next=NULL, *last=NULL;
        while ( (next=strtok_r(next?NULL:buffer,",",&last)) )
        {
            std::string value(next);
            column_name.push_back(value);
            column_index[value] = ncolumns;
            ncolumns++;
        }
    }

    // read records
    nrows = 0;
    while ( std::getline(file,line) )
    {
        char buffer[line.length()+1], *p = buffer; *p='\0';
        ROW data;
        bool quoted = false;
        bool escaped = false;
        unsigned int n = 0;
        while ( n < ncolumns )
        {
            for ( const char *c = line.c_str() ; *c != '\0' && n < ncolumns ; c++ )
            {
                if ( *c == '\\' )
                {
                    escaped = true;
                    continue;
                }
                else if ( *c == '"' && ! escaped )
                {
                    quoted = ! quoted;
                    continue;
                }
                else if ( *c == ',' && ! quoted && ! escaped )
                {
                    data.push_back(cell(buffer,as_string));
                    p = buffer;
                    n++;
                }
                else 
                {
                    escaped = false;
                    *p++ = *c;
                }
                *p = '\0';
            }
            while ( n++ < ncolumns )
            {
                data.push_back(cell(buffer,as_string));
                buffer[0] = '\0';
            }
        }
        rows.push_back(data);
        nrows++;
    }
}

void table::to_csv(const char *filename)
{
    FILE *fh = filename ? fopen(filename,"w") : stdout;
    if ( fh == NULL )
    {
        throw "table::to_csv() -- file open failed";
    }

    // dump column_index
    for ( auto f = column_name.begin() ; f != column_name.end() ; f++ )
    {
        fprintf(fh,"%s%s",f!=column_name.begin()?",":"",f->c_str());
    }
    fprintf(fh,"\n");

    // dump rows
    unsigned n = 0;
    for ( auto r = rows.begin() ; r != rows.end() ; r++ , n++ )
    {
        for ( auto m = r->begin() ; m != r->end() ; m++ )
        {
            std::string value = m->to_string();
            const char *str = value.c_str();
            const char *quote = strchr(str,',') ? "\"" : "";
            const char *sep = m==r->begin() ? "" : ",";
            fprintf(fh,"%s%s%s%s",sep,quote,str,quote);
        }
        fprintf(fh,"\n");
    }
}

void table::set_index(const char *column,...)
{
    index_names.clear();
    va_list ptr;
    va_start(ptr,column);
    while ( column != NULL )
    {
        // printf("looking for column '%s'...",column);
        std::vector<std::string>::iterator item = column_name.begin();
        for ( ; item != column_name.end() ; item++ )
            if ( *item == column)
                break;

        if ( item == column_name.end() )
        {
            gl_exception("table::set_index(const char *column='%s'): column not found",column);
        }
        index_names.push_back(column);
        unsigned int col = column_index[column];
        index_columns.push_back(col);
        // printf("column %u ok\n",col);
        column = va_arg(ptr,const char*);
    }
    unsigned int n = 0;
    for ( auto row = rows.begin() ; row != rows.end() ; row++ )
    {
        std::string value;
        for ( auto col = index_columns.begin() ; col != index_columns.end() ; col++ )
        {
            if ( col != index_columns.begin() )
            {
                value += "|";
            }
            value += (*row)[*col].to_string();
        }
        // printf("ROW[%d]: %s\n",n++,value.c_str());
        index_names.push_back(value.c_str());
        index[value.c_str()] = n;
    }
    va_end(ptr);
}

std::string table::get_index(const char *column,...)
{
    std::string result;
    va_list ptr;
    va_start(ptr,column);
    while ( column != NULL )
    {
        if ( result != "" )
        {
            result += "|";
        }
        result += column;
    }
    va_end(ptr);
    return result;
}

cell &table::at(unsigned int r, unsigned int c)
{
    table::ROW &row = load_data->at(r);
    return row.at(c);
}

cell &table::at(const char *r, unsigned int c)
{
    table::ROW &row = load_data->at(r);
    return row.at(c);
}

cell &table::at(unsigned int r, const char *c)
{
    table::ROW &row = load_data->at(r);
    return row.at(load_data->column_index[c]);
}

cell &table::at(const char *r, const char *c)
{
    table::ROW &row = load_data->at(r);
    return row.at(load_data->column_index[c]);
}

table::COLUMN table::get_column(unsigned int n)
{
    COLUMN data;
    for ( auto row = rows.begin() ; row != rows.end() ; row++ )
    {
        data.push_back(row->at(n));
    }
    return data;
}
