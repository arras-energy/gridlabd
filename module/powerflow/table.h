// module/powerflow/table.h

#ifndef _TABLE_H
#define _TABLE_H

#include "powerflow.h"

class cell
{

private: // types

    typedef enum {
        DT_VOID, // empty unquoted cell or NaN value
        DT_BOOL, // true/false std::string (any case)
        DT_INT, // integer value (not real)
        DT_DOUBLE, // real value
        DT_STRING, // std::string value (not boolean, integer, or float)
    } DATATYPE;
    
    typedef union
    {
        bool boolean;
        long long integer;
        double real;
        const char *string;
    } DATAVALUE;

public: // data

    DATATYPE type;
    DATAVALUE value;

public:  // cstor/dstor

    cell(void);
    cell(bool);
    cell(long long);
    cell(double);
    cell(const char *str, bool as_string=false);
    ~cell(void);

public: // methods

    bool to_bool(bool if_void=false);
    long long to_int(long long if_void=0);
    double to_double(double if_void=QNAN);
    std::string to_string(const char *if_void="");
    inline bool is_void() { return type == DT_VOID; };
    inline bool is_bool() { return type == DT_BOOL; };
    inline bool is_int() { return type == DT_INT; };
    inline bool is_double() { return type == DT_DOUBLE; };
    inline bool is_string() { return type == DT_STRING; };
    inline double real() { return value.real; };
    inline long long integer() { return value.integer; };
    inline bool boolean() { return value.boolean; };
    inline const char *string() { return value.string; };
};

class table
{

public: // types

    typedef std::vector<cell> ROW;
    typedef std::vector<ROW> ROWLIST;

public: // data

    unsigned int ncolumns;
    std::vector<std::string> column_name; // column names
    std::map<std::string,unsigned int> column_index; // column index
    unsigned int nrows;
    std::vector<ROW> rows; // row data
    std::vector<const char*> index_names; // index column names
    std::vector<unsigned int> index_columns; // imdex column_index numbers
    std::map<std::string,unsigned int> index; // row index

public: // cstor/dstor

    table(const char *filename, bool as_string=false);
    ~table(void);

public: // methods

    // data access
    inline ROW &operator[] (unsigned int n) { return rows[n]; };
    inline ROW &at(unsigned int n) { return rows[n]; };
    inline ROW &operator[] (const char *ndx) { return at(index[ndx]); };
    inline ROW &at(const char *ndx) { return at(index[ndx]);};
    cell &at(unsigned int r, unsigned int c);
    cell &at(const char *r, unsigned int c);
    cell &at(unsigned int r, const char *c);
    cell &at(const char *r, const char *c);
    void set_index(const char *column,...);
    std::string get_index(const char *column,...);

    // data storage
    void to_csv(const char *filename=NULL);
};

#endif // _TABLE_H