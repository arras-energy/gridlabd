/** $Id: recorder.cpp 4738 2014-07-03 00:55:39Z dchassin $
    DP Chassin - July 2012
    Copyright (C) 2012 Battelle Memorial Institute
 **/

#ifdef HAVE_MYSQL

#include <time.h>
#include "database.h"

EXPORT_CREATE(recorder);
EXPORT_INIT(recorder);
EXPORT_COMMIT(recorder);

CLASS *recorder::oclass = NULL;
recorder *recorder::defaults = NULL;

std::vector<std::string> split(char* str, const char* delim)
{
    char* saveptr;
    char* token = strtok_r(str,delim,&saveptr);

    std::vector<std::string> result;

    while(token != NULL)
    {
        result.push_back(token);
        token = strtok_r(NULL,delim,&saveptr);
    }
    return result;
}

recorder::recorder(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"recorder",sizeof(recorder),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class recorder";
		else
			oclass->trl = TRL_PROTOTYPE;

		defaults = this;
		if (gl_publish_variable(oclass,
			PT_char1024,"property",get_property_offset(),PT_DESCRIPTION,"target property name",
			PT_char32,"trigger",get_trigger_offset(),PT_DESCRIPTION,"recorder trigger condition",
			PT_char1024,"table",get_table_offset(),PT_DESCRIPTION,"table name to store samples",
			PT_char1024,"file",get_table_offset(),PT_DESCRIPTION,"file name (for tape compatibility)",
			PT_char32,"mode",get_mode_offset(),PT_DESCRIPTION,"table output mode",
			PT_int32,"limit",get_limit_offset(),PT_DESCRIPTION,"maximum number of records to output",
			PT_double,"interval[s]",get_interval_offset(),PT_DESCRIPTION,"sampling interval",
			PT_object,"connection",get_connection_offset(),PT_DESCRIPTION,"database connection",
			PT_set,"options",get_options_offset(),PT_DESCRIPTION,"SQL options",
				PT_KEYWORD,"PURGE",(set)MO_DROPTABLES,PT_DESCRIPTION,"flag to drop tables before creation",
				PT_KEYWORD,"UNITS",(set)MO_USEUNITS,PT_DESCRIPTION,"include units in column names",
				PT_KEYWORD,"NOADD",(set)MO_NOADD,PT_DESCRIPTION,"do not automatically add missing columns",
			PT_char32,"datetime_fieldname",get_datetime_fieldname_offset(),PT_DESCRIPTION,"name of date-time field",
			PT_char32,"recordid_fieldname",get_recordid_fieldname_offset(),PT_DESCRIPTION,"name of record-id field",
			PT_char1024,"header_fieldnames",get_header_fieldnames_offset(),PT_DESCRIPTION,"name of header fields to include",
			NULL)<1){
				char msg[256];
				snprintf(msg,sizeof(msg)-1, "unable to publish properties in %s",__FILE__);
				throw msg;
		}
		defaults = this;
	}
}

int recorder::create(void) 
{
	set_property("");
	set_trigger("");
	set_table("");
	limit = 0;
	interval = 0;
	connection = NULL;
	options = 0;
	strcpy(datetime_fieldname,"t");
	strcpy(recordid_fieldname,"id");
	set_header_fieldnames("");

	enabled = false;
	db = last_database;
	trigger_on = false;
	strcpy(compare_op,"");
	strcpy(compare_val,"");
	n_properties = 0;
	property_target = new std::vector<gld_property>;
	property_unit = new std::vector<gld_unit>;
	strcpy(header_data,"");
	oldvalues = NULL;
	return 1; /* return 1 on success, 0 on failure */
}

int recorder::init(OBJECT *parent)
{
	// check the connection
	if ( get_connection()!=NULL )
		db = (database*)(get_connection()+1);
	if ( db==NULL )
		exception("no database connection available or specified");
	if ( !db->isa("database") )
		exception("connection is not a mysql database");
	gl_verbose("connection to mysql server '%s', schema '%s' ok", db->get_hostname(), db->get_schema());

	// check mode
	if ( strlen(mode)>0 )
	{
		options = 0xffffffff;
		struct {
			const char *str;
			set bits;
		} modes[] = {
			{"r",	0xffff},
			{"r+",	0xffff},
			{"w",	MO_DROPTABLES},
			{"w+",	MO_DROPTABLES},
			{"a",	0x0000},
			{"a+",	0x0000},
		};
		size_t n;
		for ( n=0 ; n<sizeof(modes)/sizeof(modes[0]) ; n++ )
		{
			if ( strcmp(mode,modes[n].str)==0 )
			{
				options = modes[n].bits;
				break;
			}
		}
		if ( options==0xffffffff )
			exception("mode '%s' is not recognized",(const char*)mode);
		else if ( options==0xffff )
			exception("mode '%s' is not valid for a recorder", (const char*)mode);
	}

	// drop table if exists and drop specified
	db->table_exists(NULL); // clear last table checked
	if ( db->table_exists(get_table()) )
	{
		if ( get_options()&MO_DROPTABLES && !db->query("DROP TABLE IF EXISTS `%s`", get_table()) )
			exception("unable to drop table '%s'", get_table());
		gl_verbose("dropped table %s",get_table());
	}
	
	// create table if not exists
	gl_verbose("preparing table %s",get_table());
	db->table_exists(NULL); // clear last table checked
	if ( !db->table_exists(get_table()) )
	{
		if ( !(options&MO_NOCREATE) )
		{
			if ( !db->query("CREATE TABLE IF NOT EXISTS `%s` ("
				"`%s` INT AUTO_INCREMENT PRIMARY KEY, "
				"`%s` TIMESTAMP, "
				"INDEX `i_%s` (`%s`) "
				")", 
				get_table(),
				(const char*)recordid_fieldname,
				(const char*)datetime_fieldname,
				(const char*)datetime_fieldname, (const char*)datetime_fieldname))
				exception("unable to create table '%s' in schema '%s'", get_table(), db->get_schema());
			else
				gl_verbose("table %s created ok", get_table());
		}
		else
			exception("NOCREATE option prevents creation of table '%s'", get_table());
	}

	// check row count
	else 
	{
		if ( db->select("SELECT max(`%s`) FROM `%s`", (const char*)get_recordid_fieldname(), get_table())==NULL
				&& db->select("SELECT count(*) FROM `%s`", get_table())==NULL )
			exception("unable to get row count of table '%s'", get_table());

		gl_verbose("table '%s' ok", get_table());
	}

	// connect the target properties
	std::vector<std::string> property_specs = split(get_property(), ", \t;");
	char property_list[65536]="";
	for ( size_t n = 0 ; n < property_specs.size() ; n++ )
	{
		char buffer[1024];
		strcpy(buffer,(const char*)property_specs[n].c_str());
		std::vector<std::string> spec = split(buffer,"[]");
		if ( spec.size()>0 )
		{
			strcpy(buffer,(const char*)spec[0].c_str());
			gld_property prop;
			if ( get_parent()==NULL )
				prop = gld_property(buffer);
			else
				prop = gld_property(get_parent(),buffer);
			if ( prop.get_object()==NULL )
			{
				if ( get_parent()==NULL )
					exception("parent object is not set");
				prop = gld_property(get_parent(),buffer);
			}
			if ( !prop.is_valid() )
				exception("property %s is not valid", buffer);

			(*property_target).push_back(prop);
			debug("adding field from property '%s'", buffer);
			gld_unit unit;
			if ( spec.size()>1 )
			{
				char tmp[1024];
				strcpy(tmp,(const char*)spec[1].c_str());
				unit = gld_unit(tmp);
			}
			else if ( prop.get_unit()!=NULL && (options&MO_USEUNITS) )
				unit = *prop.get_unit();
			(*property_unit).push_back(unit);
			n_properties++;

			const char *sqltype = db->get_sqltype(prop);
			if ( sqltype==NULL )
				exception("property '%s' has an unknown SQL type", prop.get_name());

			char fieldname[1024];
			if ( unit.is_valid() )
			{
				snprintf(fieldname,sizeof(fieldname)-1,"%s[%s]", prop.get_name(), unit.get_name());
			}
			else
			{
				snprintf(fieldname,sizeof(fieldname)-1,"%s", prop.get_name());
			}
			char tmp[1030];
			snprintf(tmp,sizeof(tmp)-1,"`%s` %s, ",fieldname,sqltype);
			strcat(property_list,tmp);
			if ( db->check_field(get_table(),fieldname) ) 
				gl_verbose("column '%s' of table '%s' is ok",fieldname,get_table());
			else if ( (options&MO_NOADD)==MO_NOADD )
				gl_warning("automatic add of column '%s' to table '%s' suppressed by NOADD option",fieldname,get_table());
			else if ( db->query("ALTER TABLE `%s` ADD COLUMN `%s` %s;", get_table(), fieldname, sqltype) )
				gl_verbose("automatically added missing column '%s' as '%s' to '%s'", fieldname, sqltype, get_table());
			else 
				gl_error("unable to add column '%s' to table '%s'",fieldname,get_table());

		}
	}

	// get header fields
	if ( strlen(header_fieldnames)>0 )
	{
		if ( get_parent()==NULL )
			exception("cannot find header fields without a parent");
		char buffer[1024];
		strcpy(buffer,header_fieldnames);
		std::vector<std::string> header_specs = split(buffer, ",");
		size_t header_pos = 0;
		header_data[0] = '\0';
		for ( size_t n = 0 ; n < header_specs.size() ; n++ )
		{
			bool is_ok = db->check_field(get_table(), (const char*)header_specs[n].c_str());
			if ( header_specs[n].compare("name")==0 )
			{
				snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",'%s'",get_parent()->get_name());
				header_pos = strlen(header_data);
				strcat(property_list,"name CHAR(64), index i_name (name), ");
				if ( !is_ok && (options&MO_NOADD)==0 && db->query_ex("ALTER TABLE `%s` ADD COLUMN `name` CHAR(64);", get_table(), get_parent()->get_name()) )
					warning("automatically added missing header field 'name' to '%s'", get_table());
			}
			else if ( header_specs[n].compare("class")==0 )
			{
				snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",'%s'",get_parent()->get_oclass()->get_name());
				header_pos = strlen(header_data);
				strcat(property_list,"class CHAR(32), index i_class (class), ");
				if ( !is_ok && (options&MO_NOADD)==0 && db->query_ex("ALTER TABLE `%s` ADD COLUMN `class` CHAR(32);", get_table(), get_parent()->get_name()) )
					warning("automatically added missing header field 'class' to '%s'", get_table());
			}
			else if ( header_specs[n].compare("groupid")==0 )
			{
				snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",'%s'",get_parent()->get_groupid());
				header_pos = strlen(header_data);
				strcat(property_list,"groupid CHAR(32), index i_groupid (groupid), ");
				if ( !is_ok && (options&MO_NOADD)==0 && db->query_ex("ALTER TABLE `%s` ADD COLUMN `groupid` CHAR(32);", get_table(), get_parent()->get_name()) )
					warning("automatically added missing header field 'groupid' to '%s'", get_table());
			}
			else if ( header_specs[n].compare("latitude")==0 )
			{
				if ( isnan(get_parent()->get_latitude()) )
				{
					snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",%s","NULL");
					header_pos = strlen(header_data);
				}
				else
				{
					snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",%.6f", get_parent()->get_latitude());
					header_pos = strlen(header_data);
				}
				strcat(property_list,"latitude DOUBLE, index i_latitude (latitude), ");
				if ( !is_ok && (options&MO_NOADD)==0 && db->query_ex("ALTER TABLE `%s` ADD COLUMN `latitude` DOUBLE;", get_table(), get_parent()->get_name()) )
					warning("automatically added missing header field 'latitude' to '%s'", get_table());
			}
			else if ( header_specs[n].compare("longitude")==0 )
			{
				if ( isnan(get_parent()->get_longitude()) )
				{
					snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",%s","NULL");
					header_pos = strlen(header_data);
				}
				else
				{
					snprintf(header_data+header_pos,sizeof(header_data)-header_pos-1,",%.6s", get_parent()->get_oclass()->get_name());
					header_pos = strlen(header_data);
				}
				strcat(property_list,"longitude DOUBLE, index i_longitude (longitude), ");
				if ( !is_ok && (options&MO_NOADD)==0 && db->query_ex("ALTER TABLE `%s` ADD COLUMN `longitude` DOUBLE;", get_table(), get_parent()->get_name()) )
					warning("automatically added missing header field 'longitude' to '%s'", get_table());
			}
			else
				exception("header field %s does not exist",(const char*)header_specs[n].c_str());
		}
	}

	// set heartbeat
	if ( interval>0 )
	{
		set_heartbeat((TIMESTAMP)fabs(interval));
		enabled = true;
	}
	else if ( interval<0 )
	{
		enabled = true;
	}

	// arm trigger, if any
	if ( enabled && trigger[0]!='\0' )
	{
		// read trigger condition
		if ( sscanf(trigger,"%[<>=!]%s",compare_op,compare_val)==2 )
		{
			// enable trigger and suspend data collection
			trigger_on=true;
			enabled=false;
			debug("%s: trigger '%s' enabled", get_name(), get_trigger());
		}
	}

	// diff sampling only
	if ( interval<0 )
	{
		oldvalues = (char*)malloc(65536);
		strcpy(oldvalues,"");
	}
	else
		oldvalues = NULL;

	return 1;
}

EXPORT TIMESTAMP heartbeat_recorder(OBJECT *obj)
{
	recorder *my = OBJECTDATA(obj,recorder);
	if ( my->get_interval() < 0 ) return TS_NEVER;
	if ( !my->get_trigger_on() && !my->get_enabled() ) return TS_NEVER;
	obj->clock = gl_globalclock;
	TIMESTAMP dt = (TIMESTAMP)my->get_interval();
	
	// recorder is always a soft event
	return -(obj->clock/dt+1)*dt;
}

TIMESTAMP recorder::commit(TIMESTAMP t0, TIMESTAMP t1)
{
	// check trigger
	if ( trigger_on )
	{
		// trigger condition
		if ( (*property_target)[0].compare(compare_op,compare_val) )
		{
			// disable trigger and enable data collection
			trigger_on = false;
			enabled = true;
		}
	}
	else if ( trigger[0]=='\0' )
		enabled = true;

	// check sampling interval
	debug("%s: interval=%.0f, clock=%lld", get_name(), interval, gl_globalclock);
	if ( interval!=0 )
	{
		if ( gl_globalclock%((TIMESTAMP)fabs(interval))!=0 )
			return TS_NEVER;
		else
			gl_verbose("%s: sampling time has arrived", get_name());
	}

	// collect data
	if ( enabled )
	{
		char fieldlist[65536] = "", valuelist[65536] = "";
		size_t fieldlen = 0;
		if ( header_fieldnames[0]!='\0' )
		{
			snprintf(fieldlist,sizeof(fieldlist)-1,",%s",(const char*)header_fieldnames);
			fieldlen = strlen(fieldlist);
		}
		strcpy(valuelist,header_data);
		size_t valuelen = strlen(valuelist);
		for ( size_t n = 0 ; n < (*property_target).size() ; n++ )
		{
			char buffer[1024] = "NULL";
			if ( (*property_unit)[n].is_valid() )
			{
				snprintf(fieldlist+fieldlen,sizeof(fieldlist)-fieldlen-1,",`%s[%s]`", (*property_target)[n].get_name(), (*property_unit)[n].get_name());
				fieldlen = strlen(fieldlist);
			}
			else
			{
				snprintf(fieldlist+fieldlen,sizeof(fieldlist)-fieldlen-1,",`%s`", (*property_target)[n].get_name());
				fieldlen = strlen(fieldlist);
			}
			db->get_sqldata(buffer, sizeof(buffer), (*property_target)[n], &(*property_unit)[n]);
			snprintf(valuelist+valuelen,sizeof(valuelist)-valuelen-1,", %s", buffer);
			valuelen = strlen(valuelist);
		}
		if ( oldvalues )
		{
			if ( strcmp(oldvalues,valuelist)==0 )
			{
				debug("diff sampling--no change to [%s]",oldvalues+1);
				return TS_NEVER;
			}
			else
			{
				debug("diff sampling--recording change from [%s] to [%s]",oldvalues+1,valuelist+1);
				strcpy(oldvalues,valuelist);
			}
		}
		db->query("INSERT INTO `%s` (`%s`%s) VALUES (from_unixtime('%" FMT_INT64 "d')%s)",
			get_table(), (const char*)datetime_fieldname, fieldlist, db->convert_to_dbtime(gl_globalclock),  valuelist);


		// check limit
		if ( get_limit() > 0 && db->get_last_index() >= (size_t)get_limit() )
		{
			// shut off recorder
			enabled=false;
			gl_verbose("table '%s' size limit %d reached", get_table(), get_limit());
		}
	}
	else
		debug("%s: sampling is not enabled", get_name());
	
	return TS_NEVER;
}

#endif // HAVE_MYSQL
