// module/pypower/geodata.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "pypower.h"

EXPORT_CREATE(geodata);
EXPORT_INIT(geodata);
EXPORT_PRECOMMIT(geodata);

CLASS *geodata::oclass = NULL;
geodata *geodata::defaults = NULL;

static MODULE *this_module = NULL;

static const char geocode_decodemap[] = "0123456789bcdefghjkmnpqrstuvwxyz";
static const unsigned char *geocode_encodemap = NULL;
// static const char *geocode_encode(char *buffer, int len, double lat, double lon, int resolution=6);
static bool geocode_decode(double *lat, double *lon, const char *code);

geodata::geodata(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"geodata",sizeof(geodata),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class geodata";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_char1024, "file", get_file_offset(),
				PT_DESCRIPTION, "geodata file name",

			PT_char256, "target", get_target_offset(),
				PT_DESCRIPTION, "geodata target class and property, e.g., CLASS:PROPERTY",

			NULL)<1)
		{
				throw "unable to publish geodata properties";
		}

		this_module = module;
	}
}

int geodata::create(void) 
{
	n_locations = 0;
	locations = NULL;
	data = NULL;
	n_data = 0;
	cur_data = 0;

	return 1; /* return 1 on success, 0 on failure */
}

int geodata::init(OBJECT *parent)
{
	// load locations
	if ( ! load_geodata(get_file()) )
	{
		error("unable to load geodata file '%s'",(const char*)get_file());
		return 0;
	}

	// get targets
	if ( get_target()[0] == '\0' )
	{
		error("target is not specified");
		return 0;
	}
	char *next=NULL, *last=NULL;
	char buffer[strlen(get_target())+1];
 	strcpy(buffer,get_target());
	while ( (next=strtok_r(next?NULL:buffer,",",&last)) != NULL )
	{
		// get geodata targets
		char classname[65];
		char objname[65];
		char propname[65];
		if ( sscanf(next,"%[^:]::%[^\n]",classname,propname) == 2 )
		{
			// check target class
			CLASS *oclass;
			for ( oclass = gl_class_get_first() ; oclass != NULL && oclass->module == this_module ; oclass = oclass->next )
			{
				if ( strcmp(oclass->name,classname) == 0 && strcmp(oclass->module->name,"pypower") == 0 )
				{
					break;
				}
			}
			if ( oclass == NULL )
			{
				error("class '%s' is not valid",classname);
				return 0;
			}

			// find objects at locations
			for ( OBJECT *obj = gl_object_get_first() ; obj != NULL ; obj = obj->next )
			{
				if ( obj->oclass == oclass )
				{
					if ( ! isnan(obj->latitude) && ! isnan(obj->longitude) )
					{
						if ( ! add_target(obj,propname) )
						{
							error("unable to find property '%s' in object '%s'",propname,(const char*)(get_object(obj)->get_name()));
							return 0;
						}
					}
					else
					{
						warning("object '%s' does not have any geodata to locate it",(const char*)get_object(obj)->get_name());
					}
				}
			}
		}
		else if ( sscanf(next,"%[^.].%[^\n]",objname,propname) == 2 )
		{
			OBJECT *obj = get_object(objname)->my();
			if ( obj == NULL )
			{
				error("object '%s' not found",objname);
				return 0;
			}
			if ( ! isnan(obj->latitude) && ! isnan(obj->longitude) )
			{
				if ( ! add_target(obj,propname) )
				{
					error("unable to find property '%s' in object '%s'",propname,objname);
					return 0;
				}
			}
			else
			{
				warning("object '%s' does not have any geodata to locate it",objname);
			}
		}
		else
		{
			error("target '%s' is not valid",next);
			return 0;
		}
	}

	return 1;
}

TIMESTAMP geodata::precommit(TIMESTAMP t0)
{
	set_time(t0);
	return get_time();
}

bool geodata::add_target(OBJECT *obj,const char *propname)
{
	gld_property *prop = new gld_property(obj,propname);
	if ( ! prop->is_valid() )
	{
		return false;
	}

	int location = find_location(obj->latitude,obj->longitude);
	if ( location < 0 )
	{
		warning("ignoring object '%s', location cannot be found in geodata file",(const char *)get_object(obj)->get_name());
		return true;
	}

	double *value = (double*)prop->get_addr();
	// fprintf(stderr,"geodata::add_target(obj='%s',propname='%s'): value@%p = %.4g\n",obj->name,propname,value,*value);
	for ( size_t n = 0 ; n < locations[location].n_values ; n++ )
	{
		if ( locations[location].values[n] == value )
		{
			warning("ignoring duplicate reference to object '%s.%s'",(const char *)get_object(obj)->get_name(),propname);
			return true;
		}
	}
	if ( locations[location].n_values >= locations[location].max_values )
	{
		locations[location].max_values *= 2;
		locations[location].values = (double**)realloc(locations[location].values,sizeof(double*)*locations[location].max_values);
	}
	locations[location].values[locations[location].n_values++] = value;
	return true;
}

size_t geodata::find_location(const char *geocode,bool exact)
{
	for ( size_t location = 0 ; location < n_locations ; location++ )
	{
		if ( exact && strcmp(geocode,locations[location].hash) == 0 )
		{
			return location;
		}
	}
	double lat,lon;
	geocode_decode(&lat,&lon,geocode);
	return find_location(lat,lon);
}

size_t geodata::find_location(double lat, double lon)
{
	int best_loc = -1;
	double best_d2 = 0;
	size_t location;
	for ( location = 0 ; location < n_locations ; location++ )
	{
		double dx = locations[location].latitude - lat;
		double dy = locations[location].longitude - lon;
		double d2 = dx*dx + dy*dy;
		if ( best_loc == -1 || d2 < best_d2 )
		{
			best_loc = location;
			best_d2 = d2;
		}
	}
	return best_loc;
}

TIMESTAMP geodata::get_time()
{
	return cur_data < n_data ? data[cur_data].timestamp : TS_NEVER;
}

double geodata::get_value(size_t location)
{
	return data[cur_data].value[location];
}

bool geodata::set_time(TIMESTAMP t0)
{
	// end of data check
	if ( t0 == TS_NEVER )
	{
		cur_data = n_data;
		return true;
	}

	// look for data
	// fprintf(stderr,"getodata::set_time(TIMESTAMP t0=%lld): current data row %zu at time %lld\n",t0,cur_data,get_time());
	while ( get_time() < t0 && cur_data < n_data )
	{
		cur_data++;
		// fprintf(stderr,"getodata::set_time(TIMESTAMP t0=%lld): advancing to data row %zu at time %lld\n",t0,cur_data,get_time());
	}
	if ( get_time() == TS_NEVER )
	{
		// fprintf(stderr,"getodata::set_time(TIMESTAMP t0=%lld): end of data\n",t0);
		return true;
	}

	// copy data
	for ( size_t location = 0 ; location < n_locations ; location++ )
	{
		GEOCODE &geocode = locations[location];
		double value = get_value(location);
		for ( size_t n = 0 ; n < geocode.n_values ; n++ )
		{
			// fprintf(stderr,"getodata::set_time(TIMESTAMP t0=%lld): updating value %.4g@%p to %.4g for time %lld from location '%s' to target %ld\n",t0,*(geocode.values[n]),geocode.values[n],value,get_time(),locations[location].hash,n);
			*(geocode.values[n]) = value;
		}
	}

	// return exact match time
	return get_time() == t0;
}

bool geodata::load_geodata(const char *file)
{
	// open geodata file
	FILE *fp = fopen((const char*)get_file(),"r");
	if ( fp == NULL )
	{
		error("file '%s' is not %s", (const char*)get_file(), get_file()[0]=='\0'?"specified":"found");
		return false;
	}

	// read data
	char line[65536*16];
	size_t max_data = 0;
	for ( size_t line_no = 0 ; ! feof(fp) && ! ferror(fp) && fgets(line,sizeof(line)-1,fp) != NULL ; line_no++ )
	{
		if ( n_locations == 0 ) // first line contains locations
		{
			size_t max_locations = 1024;
			char *next=NULL, *last=NULL;
			while ( (next=strtok_r(next?NULL:line,",",&last)) != NULL )
			{				
				if ( locations == NULL )
				{
					if ( strcmp(next,"timestamp") != 0 )
					{
						error("column 0 must be 'timestamp', but found '%s' instead",next);
						return false;
					}
					locations = (GEOCODE*)malloc(sizeof(GEOCODE)*max_locations);
				}
				else
				{
					for ( char *eos = next + strlen(next) - 1 ; eos >= next && strchr(geocode_decodemap,next[strlen(next)-1]) == NULL ; eos-- )
					{
						*eos = '\0';
					}
					if ( n_locations >= max_locations )
					{
						max_locations *= 2;
						locations = (GEOCODE*)realloc(locations,sizeof(GEOCODE)*max_locations);
					}
					if ( ! geocode_decode(&locations[n_locations].latitude,&locations[n_locations].longitude,next) )
					{
						error("geocode '%s' is not valid",next);
					}
					strncpy(locations[n_locations].hash,next,sizeof(locations[n_locations].hash)-1);
					locations[n_locations].max_values = 8;
					locations[n_locations].values = (double**)malloc(sizeof(double*)*locations[n_locations].max_values);
					locations[n_locations].n_values = 0;
					n_locations++;
				}
			}
		}
		else
		{
			char *next=NULL, *last=NULL;
			int location = -1;
			if ( n_data >= max_data )
			{
				max_data = ( max_data == 0 ? 8784 : max_data*2 );
				data = (GEODATA*)realloc(data,sizeof(GEODATA)*max_data);
			}
			while ( (next=strtok_r(next?NULL:line,",",&last)) != NULL )
			{
				if ( location < 0 ) // new line
				{
					gld_clock dt(next);
					if ( ! dt.is_valid() )
					{
						error("(%s:%ld) invalid timestamp '%s'",file,line_no,next);
						return false;
					}
					data[n_data].timestamp = dt.get_timestamp();
					data[n_data].value = (double*)malloc(sizeof(double)*n_locations);
				}
				else if ( location < (int)n_locations ) // new column
				{
					if ( sscanf(next,"%lf",&(data[n_data].value[location])) != 1 )
					{
						error("(%s:%ld) invalid float value '%s'",file,line_no,next);
					}
				}
				else // overrun column
				{
					error("(%s:%ld) unexpected extra data (location %ld > n_locations %ld)",file,line_no,location,n_locations);
					return false;
				}
				location++;
			}	
			n_data++;		
		}
	}
	return true;
}

// static const char *geocode_encode(char *buffer, int len, double lat, double lon, int resolution)
// {
// 	if ( len < resolution+1 )
// 	{
// 		output_warning("geocode_encode(buffer=%p, len=%d, lat=%g, lon=%g, resolution=%d): buffer too small for specified resolution, result truncated", 
// 			buffer, len, lat, lon, resolution);
// 		resolution = len-1;
// 	}
// 	double lat_interval[] = {-90,90};
// 	double lon_interval[] = {-180,180};
// 	char *geohash = buffer;
// 	geohash[0] = '\0';
// 	int bits[] = {16,8,4,2,1};
// 	int bit = 0;
// 	int ch = '\0';
// 	bool even = true;
// 	int i = 0;
// 	while ( i < resolution )
// 	{
// 		if ( even )
// 		{
// 			double mid = (lon_interval[0]+lon_interval[1])/2;
// 			if ( lon > mid )
// 			{
// 				ch |= bits[bit];
// 				lon_interval[0] = mid;
// 			}
// 			else
// 			{
// 				lon_interval[1] = mid;
// 			}
// 		}
// 		else
// 		{
// 			double mid = (lat_interval[0]+lat_interval[1])/2;
// 			if ( lat > mid )
// 			{
// 				ch |= bits[bit];
// 				lat_interval[0] = mid;
// 			}
// 			else
// 			{
// 				lat_interval[1] = mid;
// 			}
// 		}
// 		even = !even;
// 		if ( bit < 4 )
// 		{
// 			bit += 1;
// 		}
// 		else
// 		{
// 			*geohash++ = geocode_decodemap[ch];
// 			i++;
// 			bit = 0;
// 			ch = 0;
// 		}
// 	}
// 	*geohash++ = '\0';
// 	return buffer;
// }

static bool geocode_decode(double *lat, double *lon, const char *code)
{
	double lat_err = 90, lon_err = 180;
	double lat_interval[] = {-lat_err,lat_err};
	double lon_interval[] = {-lon_err,lon_err};
	bool is_even = true;
	size_t maxlen = strlen(geocode_decodemap);
	if ( geocode_encodemap == NULL )
	{
		static unsigned char map[256];
		for ( size_t p = 0 ; p < maxlen ; p++ )
		{
			int c = (int)geocode_decodemap[p];
			map[c] = p+1; 
			if ( c >= 'a' && c <= 'z' )
			{
				map[c + 'A' - 'a'] = map[c];
			}
		}
		geocode_encodemap = map;
	}
	const char *c = NULL;
	for ( c = code ; *c != '\0' ; c++ )
	{
		int cd = geocode_encodemap[(size_t)*c] - 1;
		if ( cd < 0 )
		{
			return false;
		}
		for ( int mask = 16 ; mask > 0 ; mask /= 2 )
		{
			if ( is_even )
			{
				lon_err /= 2;
				lon_interval[cd&mask?0:1] = (lon_interval[0] + lon_interval[1])/2;
			}
			else
			{
				lat_err /= 2;
				lat_interval[cd&mask?0:1] = (lat_interval[0] + lat_interval[1])/2;
			}
			is_even = ! is_even;
		}
	}
	*lat = (lat_interval[0] + lat_interval[1])/2;
	*lon = (lon_interval[0] + lon_interval[1])/2;
	return true;
}
