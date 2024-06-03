// module/tape/multiplayer.cpp

#include "multiplayer.h"

EXPORT_CREATE(multiplayer);
EXPORT_INIT(multiplayer);
EXPORT_PRECOMMIT(multiplayer);

EXPORT_METHOD(multiplayer,file);
EXPORT_METHOD(multiplayer,property)

CLASS *multiplayer::oclass = NULL;
multiplayer *multiplayer::defaults = NULL;

multiplayer::multiplayer(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"multiplayer",sizeof(multiplayer),PC_AUTOLOCK|PC_OBSERVER);
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
	target_list = new std::list<gld_property>();
	property_list = new std::string("");
	return 1; /* return 1 on success, 0 on failure */
}

int multiplayer::init(OBJECT *parent)
{
	if ( fp == NULL )
	{
		error("no input file specified");
	}
	if ( target_list->size() == 0 )
	{
		error("no targets specified");
	}
	return 1;
}

TIMESTAMP multiplayer::precommit(TIMESTAMP t1)
{
	return TS_NEVER;
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
			free((void*)fname);
		}
		fname = strdup(buffer);
		if ( fp != NULL )
		{
			fclose(fp);
		}
		fp = fopen(fname,"r");
		if ( fp == NULL )
		{
			error("file '%s' not found",fname);
			return 0;
		}
		else if ( ! load() )
		{
			error("unable to load file '%s'", fname);
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
	strcpy(line,buffer);
	if ( line[len-1] == '\n' )
	{
		line[len-1] = '\0'
	}

	return true;
}