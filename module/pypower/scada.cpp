// module/pypower/scada.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(scada);
EXPORT_INIT(scada);
EXPORT_PRECOMMIT(scada);
EXPORT_COMMIT(scada);
EXPORT_METHOD(scada,point);

CLASS *scada::oclass = NULL;
scada *scada::defaults = NULL;

// static int watch_dict(PyDict_WatchEvent event, PyObject *dict, PyObject *key, PyObject *new_value)
// {
// 	if ( event == PyDict_EVENT_MODIFIED )
// 	{
// 		warning("ignoring changes to scada object with write_ok not enabled");
// 	}
// }
// int watcher_id = 0;

scada::scada(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"scada",sizeof(scada),PC_POSTTOPDOWN|PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class scada";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_bool, "write", get_write_ok_offset(),
				PT_DESCRIPTION, "Enable write to point",

			PT_bool, "record", get_record_on_offset(),
				PT_DESCRIPTION, "Enable recording of point to historian",

			PT_method, "point", get_point_offset(),
				PT_DESCRIPTION, "Enable access to point specified as object <name>:<property>",

			NULL) < 1 )
		{
				throw "unable to publish scada properties";
		}
		// watcher_id = PyDict_AddWatcher(watch_dict);
	}
}

int scada::create(void) 
{
	py_controller = NULL;
	py_scada = PyDict_New();
	py_historian = PyDict_New();
	
	n_points = 0;
	max_points = 1024;
	point_list = (gld_property**)malloc(sizeof(gld_property*)*max_points);
	name_list = (char **)malloc(sizeof(char*)*max_points);
	point_names = (char*)malloc(1);
	point_names[0] = '\0';

	return 1; // return 1 on success, 0 on failure
}

int scada::init(OBJECT *parent)
{
	extern PyObject *py_globals;
	if ( py_globals == NULL )
	{
		error("unable to find global controllers");
		return 0;
	}

	// link to controller globals
	PyObject *global_scada = PyDict_GetItemString(py_globals,"scada");
	if ( global_scada == NULL )
	{
		global_scada = PyDict_New();
		PyDict_SetItemString(py_globals,"scada",global_scada);
	}
	PyDict_SetItemString(global_scada,get_name(),py_scada);

	PyObject *global_historian = PyDict_GetItemString(py_globals,"historian");
	if ( global_historian == NULL )
	{
		global_historian = PyDict_New();
		PyDict_SetItemString(py_globals,"historian",global_historian);
	}
	if ( record_on )
	{
		PyDict_SetItemString(global_historian,get_name(),py_historian);
	}

	for ( size_t n = 0 ; n < n_points ; n++ )
	{
		gld_property *prop = point_list[n];
		if ( prop == NULL || ! prop->is_valid() )
		{
			prop = new gld_property(name_list[n]);
			if ( prop == NULL )
			{
				error("scada point '%s' not found, point will be ignored", name_list[n]);
			}
			else
			{
				point_list[n] = prop;
			}
		}
	}
	// if ( ! write_ok )
	// {
	// 	PyDict_Watch(watcher_id,py_scada);
	// }

	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP scada::precommit(TIMESTAMP t0)
{
	// read property to scada object
	for ( size_t n = 0 ; n < n_points ; n++ )
	{
		gld_property *prop = point_list[n];
		if ( prop != NULL && prop->is_valid() )
		{
			char value[1025];
			if ( prop->to_string(value,sizeof(value)-1) > 0 )
			{
				PyObject *str = PyUnicode_FromString(value);
				Py_INCREF(str);
				PyDict_SetItemString(py_scada,name_list[n],str);
			}
		}
	}

	if ( record_on )
	{
		// record latest properties to historian object
		PyDict_SetItem(py_historian,PyLong_FromLong(t0),PyDict_Copy(py_scada));
	}

	return TS_NEVER;
}

TIMESTAMP scada::commit(TIMESTAMP t0, TIMESTAMP t1)
{
	if ( write_ok )
	{
		// write scada values to properties
		for ( size_t n = 0 ; n < n_points ; n++ )
		{
			gld_property *prop = point_list[n];
			if ( prop != NULL && prop->is_valid()  )
			{
				PyObject *value = PyDict_GetItemString(py_scada,name_list[n]);
				PyObject *vstr = value ? PyUnicode_AsEncodedString(value,"utf-8","~E~") : NULL;
				const char *str = vstr ? PyBytes_AS_STRING(vstr) : NULL;
				if ( str == NULL )
				{
					error("scada write of %s = '%s' failed",name_list[n],str);
				}
				else if ( prop->from_string(str) < 0 )
				{
					error("scada write of %s = '%s' invalid",name_list[n],str);
				}
				Py_XDECREF(value);
				Py_XDECREF(vstr);
			}
		}
	}
	return TS_NEVER;
}

int scada::point(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		return strlen(point_names);
	}
	else if ( len == 0 )
	{
		// read data from buffer
		if ( n_points == max_points )
		{
			max_points *= 2;
			point_list = (gld_property**)realloc(point_list,max_points);
			name_list = (char**)realloc(name_list,max_points);
		}
		point_list[n_points] = new gld_property(buffer);
		name_list[n_points] = strdup(buffer);
		if ( point_list[n_points] == NULL || name_list[n_points] == NULL )
		{
			return 0;
		}
		n_points++;

		// copy name to list of names
		int pos = strlen(point_names);
		len = strlen(buffer);
		point_names = (char*)realloc(point_names,pos+len+2);
		return snprintf(point_names+pos,len+1,",%s",buffer);
	}
	else
	{
		return snprintf(buffer,len-1,"%s",point_names);
	}
}