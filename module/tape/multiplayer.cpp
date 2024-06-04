// module/tape/multiplayer.cpp

#include "multiplayer.h"

EXPORT_CREATE(multiplayer);
EXPORT_INIT(multiplayer);
EXPORT_PRECOMMIT(multiplayer);
EXPORT_SYNC(multiplayer);

EXPORT_METHOD(multiplayer,file);
EXPORT_METHOD(multiplayer,property)

CLASS *multiplayer::oclass = NULL;
multiplayer *multiplayer::defaults = NULL;

multiplayer::multiplayer(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"multiplayer",sizeof(multiplayer),PC_BOTTOMUP|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class multiplayer";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_enumeration, "status", get_status_offset(), 
				PT_DEFAULT, "INIT",  
				PT_DESCRIPTION, "status of multiuplayer",
				PT_KEYWORD, "INIT", (enumeration)MS_INIT,
				PT_KEYWORD, "OK", (enumeration)MS_OK,
				PT_KEYWORD, "DONE", (enumeration)MS_DONE,
				PT_KEYWORD, "ERROR", (enumeration)MS_ERROR,

			PT_char32, "indexname", get_indexname_offset(),
				PT_DEFAULT, "timestamp",
				PT_DESCRIPTION, "name of index column",

			PT_enumeration, "on_error", get_on_error_offset(),
				PT_DEFAULT, "WARN",
				PT_KEYWORD, "IGNORE", (enumeration)ERR_IGNORE,
				PT_KEYWORD, "WARN", (enumeration)ERR_WARN,
				PT_KEYWORD, "STOP", (enumeration)ERR_STOP,
				PT_DESCRIPTION, "error handling (IGNORE, WARN, STOP)",

			PT_method, "file", get_file_offset(),
				PT_DESCRIPTION, "data source",

			PT_method, "property", get_property_offset(),
				PT_DESCRIPTION, "target property or object:property",

			NULL)<1)
		{
			exception("unable to publish multiplayer properties");
		}
	}
}

int multiplayer::create(void) 
{
	fname = NULL;
	fp = NULL;
	maxlen = 1024;
	line = (char*)malloc(maxlen);
	target_list = new std::list<gld_property>();
	property_list = new std::string("");
	next_t = TS_ZERO;
	status = MS_INIT;
	return 1; /* return 1 on success, 0 on failure */
}

int multiplayer::init(OBJECT *parent)
{
	if ( fp == NULL )
	{
		error("no input file specified");
	}
	if ( ! load() )
	{
		error("unable to load file '%s'", fname);
		return 0;
	}
	if ( target_list->size() == 0 )
	{
		error("no targets specified");
	}

	return 1;
}

TIMESTAMP multiplayer::precommit(TIMESTAMP t1)
{
	if ( t1 < next_t )
	{
		return next_t;
	}
	char *last;
	char *next = strtok_r(line,",",&last);
	if ( next == NULL && target_list->size() > 0 )
	{
		error("no data on record at index '%s'", line);
		status = MS_ERROR;
		return TS_INVALID;
	}
	char *ts = next;
	std::list<gld_property>::iterator prop = target_list->begin();
	while ( (next=strtok_r(NULL,",",&last)) != NULL && prop != target_list->end() )
	{
		if ( prop->from_string(next) <= 0 )
		{
			switch ( on_error )
			{
			case ERR_STOP:
				error("unable to set '%s.%s' to value '%s'",get_object(prop->get_object())->get_name(),prop->get_name(),next);
				status = MS_ERROR;
				return TS_INVALID;
			case ERR_WARN:
				warning("ignoring unable to set '%s.%s' to value '%s'",get_object(prop->get_object())->get_name(),prop->get_name(),next);					
				status = MS_ERROR;
				break;
			case ERR_IGNORE:
			default:
				status = next_t < TS_NEVER ? MS_OK : MS_DONE;
				break;
			}
		}
		prop++;
	}
	if ( strtok_r(NULL,",",&last) != NULL )
	{
		switch ( on_error )
		{
		case ERR_STOP:
			error("extra data '%s' at index '%s'",next,ts);
			status = MS_ERROR;
			return TS_INVALID;
		case ERR_WARN:
			warning("ignoring extra data '%s' at index '%s'",next,ts);
			status = MS_ERROR;
			break;
		case ERR_IGNORE:
		default:
			status = next_t < TS_NEVER ? MS_OK : MS_DONE;
			break;
		}		
	}
	else if ( prop != target_list->end() )
	{
		switch ( on_error )
		{
		case ERR_STOP:
			error("missing data for '%s.%s' at index '%s'",get_object(prop->get_object())->get_name(),prop->get_name(),ts);
			status = MS_ERROR;
			return TS_INVALID;
		case ERR_WARN:
			warning("ignoring missing data for '%s.%s' at index '%s'",get_object(prop->get_object())->get_name(),prop->get_name(),ts);
			status = MS_ERROR;
			break;
		case ERR_IGNORE:
		default:
			status = next_t < TS_NEVER ? MS_OK : MS_DONE;
			break;
		}		
	}

	return read() ? next_t : TS_INVALID;
}

TIMESTAMP multiplayer::presync(TIMESTAMP t1)
{
	return TS_INVALID;
}

TIMESTAMP multiplayer::sync(TIMESTAMP t1)
{
	return next_t;
}

TIMESTAMP multiplayer::postsync(TIMESTAMP t1)
{
	return TS_INVALID;
}

int multiplayer::property(char *buffer, size_t len)
{
	if ( buffer == NULL ) // get length of copy to buffer result
	{
		return property_list->size()+1;
	}
	else if ( len == 0 ) // copy from buffer
	{
		char *next=NULL, *last=NULL;
		size_t total_len = strlen(buffer);
		while ( (next=strtok_r(next?NULL:buffer,",",&last)) != NULL )
		{
			gld_property *prop = get_parent() == NULL ? new gld_property(next) : new gld_property(get_parent(),next);
			if ( prop->is_valid() )
			{
				target_list->insert(target_list->end(),*prop);
				if ( property_list->size() > 0 )
				{
					property_list->append(",");
				}
				property_list->append(next);
			}
			else
			{
				error("property '%s' is not found",next);
				return 0;
			}
		}
		return total_len;		
	}
	else // copy to buffer
	{
		if ( len > property_list->size() )
		{
			strcpy(buffer,property_list->c_str());
			return property_list->size()+1;
		}
		else
		{
			return -1;
		}
	}
	return -1;	
}

int multiplayer::file(char *buffer, size_t len)
{
	if ( buffer == NULL ) // get length of copy to buffer result
	{
		return strlen(fname)+1;
	}
	else if ( len == 0 ) // copy from buffer
	{
		if ( fname != NULL )
		{
			error("unable to change the file after it is loaded");
			return 0;
		}
		fname = strdup(buffer);
		fp = fopen(fname,"r");
		if ( fp == NULL )
		{
			error("file '%s' not found",fname);
			return 0;
		}
		return strlen(fname)+1;
	}
	else // copy to buffer
	{
		return snprintf(buffer,len-1,"%s",fname)+1;
	}
	return -1;
}

bool multiplayer::load(void)
{
	fseek(fp,0,SEEK_SET);
	size_t len;
	char *buffer = fgetln(fp,&len);
	char line[len+1];
	strncpy(line,buffer,len);
	line[len] = '\0';
	if ( line[len-1] == '\n' )
	{
		line[len-1] = '\0';
	}
	if ( target_list->size() > 0 )
	{
		return read();
	}
	char *last=NULL;
	char *next=strtok_r(line,",",&last);
	if ( next == NULL || strcmp(next,indexname)!=0 )
	{
		error("column '%s' is not '%s' as specified by indexname property",next?next:"0",(const char *)indexname);
		return false;
	}
	while ( (next=strtok_r(NULL,",",&last)) != NULL )
	{
		if ( property(next,0) <= 0 )
		{
			error("file load failed");
			return false;
		}
	}
	return read();
}

bool multiplayer::read(void)
{
	if ( ferror(fp) )
	{
		status = MS_ERROR;
		return false;
	}
	if ( feof(fp) )
	{
		next_t = TS_NEVER;
		return true;
	}
	size_t len;
	char *buffer = fgetln(fp,&len);
	if ( len+1 > maxlen )
	{
		line = (char*)realloc(line,maxlen*=2);
	}
	strncpy(line,buffer,len);
	line[len] = '\0';
	if ( line[len-1] == '\n' )
	{
		line[len-1] = '\0';
	}
	TIMESTAMP last_t = next_t;
	next_t = gld_clock(line).get_timestamp();
	if ( next_t == TS_ZERO )
	{
		next_t = last_t; // no new data
		return true;
	}
	else if ( next_t <= last_t )
	{
		error("invalid index (out of order) at '%s'",line);
		status = MS_ERROR;
		return false;
	}
	else
	{
		return true;
	}
}