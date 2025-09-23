// module/powerflow/triplex_zipload.cpp
// Copyright (C) 2025 Eudoxys Sciences LLC

#include "powerflow.h"

EXPORT_CREATE(triplex_zipload);
EXPORT_INIT(triplex_zipload);
EXPORT_PRECOMMIT(triplex_zipload);
EXPORT_SYNC(triplex_zipload);

CLASS *triplex_zipload::oclass = NULL;
CLASS *triplex_zipload::pclass = NULL;
triplex_zipload *triplex_zipload::defaults = NULL;

// timestamp cache
TIMESTAMP triplex_zipload::now = 0;
unsigned int triplex_zipload::month = 0;
unsigned int triplex_zipload::weekday = 0;
unsigned int triplex_zipload::hour = 0;

triplex_zipload::triplex_zipload(MODULE *mod) : triplex_load(mod)
{
	if(oclass == NULL){
		pclass = load::oclass;

		oclass = gl_register_class(mod, 
			"triplex_zipload", 
			sizeof(triplex_zipload),
			PC_PRETOPDOWN|PC_BOTTOMUP|PC_POSTTOPDOWN|PC_UNSAFE_OVERRIDE_OMIT|PC_AUTOLOCK);
		if ( oclass==NULL )
		{
			throw "unable to register class triplex_zipload";
		}
		else
		{
			oclass->trl = TRL_PROTOTYPE;
		}

		if ( gl_publish_variable(oclass,
			PT_INHERIT, "triplex_load",
			PT_char32,"load_type", PADDR(load_type),
				PT_DESCRIPTION, "load type for triplex_zipload load parameter look-up",
			PT_object, "weather", PADDR(weather),
			PT_double, "Theat[degF]", PADDR(Theat),
			PT_double, "Tcool[degF]", PADDR(Tcool),
			PT_double, "Pz_H[W/degF]", PADDR(imped_p[0]),
			PT_double, "Pz_C[W/degF]", PADDR(imped_p[1]),
			PT_double, "Pz_S[m^2]", PADDR(imped_p[2]),
			PT_double, "Pz_W[W/mph]", PADDR(imped_p[3]),
			PT_double, "Pz_R[W*h/in]", PADDR(imped_p[4]),
			PT_double, "Pz[W]", PADDR(imped_p[5]),
			PT_double, "Qz_H[VAr/degF]", PADDR(imped_q[0]),
			PT_double, "Qz_C[VAr/degF]", PADDR(imped_q[1]),
			PT_double, "Qz_S[VAr*h/Btu]", PADDR(imped_q[2]),
			PT_double, "Qz_W[VAr/mph]", PADDR(imped_q[3]),
			PT_double, "Qz_R[VAr*h/in]", PADDR(imped_q[4]),
			PT_double, "Qz[VAr]", PADDR(imped_q[5]),
			PT_double, "Pi_H[W/degF]", PADDR(current_p[0]),
			PT_double, "Pi_C[W/degF]", PADDR(current_p[1]),
			PT_double, "Pi_S[m^2]", PADDR(current_p[2]),
			PT_double, "Pi_W[W/mph]", PADDR(current_p[3]),
			PT_double, "Pi_R[W*h/in]", PADDR(current_p[4]),
			PT_double, "Pi[W]", PADDR(current_p[5]),
			PT_double, "Qi_H[VAr/degF]", PADDR(current_q[0]),
			PT_double, "Qi_C[VAr/degF]", PADDR(current_q[1]),
			PT_double, "Qi_S[m^2]", PADDR(current_q[2]),
			PT_double, "Qi_W[VAr/mph]", PADDR(current_q[3]),
			PT_double, "Qi_R[VAr*h/in]", PADDR(current_q[4]),
			PT_double, "Qi[VAr]", PADDR(current_q[5]),
			PT_double, "Pp_H[W/degF]", PADDR(power_p[0]),
			PT_double, "Pp_C[W/degF]", PADDR(power_p[1]),
			PT_double, "Pp_S[m^2]", PADDR(power_p[2]),
			PT_double, "Pp_W[W/mph]", PADDR(power_p[3]),
			PT_double, "Pp_R[W*h/in]", PADDR(power_p[4]),
			PT_double, "Pp[W]", PADDR(power_p[5]),
			PT_double, "Qp_H[VAr/degF]", PADDR(power_q[0]),
			PT_double, "Qp_C[VAr/degF]", PADDR(power_q[1]),
			PT_double, "Qp_S[m^2]", PADDR(power_q[2]),
			PT_double, "Qp_W[VAr/mph]", PADDR(power_q[3]),
			PT_double, "Qp_R[VAr*h/in]", PADDR(power_q[4]),
			PT_double, "Qp[VAr]", PADDR(power_q[5]),
			PT_double, "H[degF]", PADDR(input[0]), PT_ACCESS, PA_REFERENCE,
			PT_double, "C[degF]", PADDR(input[1]), PT_ACCESS, PA_REFERENCE,
			PT_double, "S[kW]", PADDR(input[2]), PT_ACCESS, PA_REFERENCE,
			PT_double, "W[mph]", PADDR(input[3]), PT_ACCESS, PA_REFERENCE,
			PT_double, "R[in/h]", PADDR(input[4]), PT_ACCESS, PA_REFERENCE,
			PT_complex, "Z[ohm]", PADDR(Z), PT_ACCESS, PA_REFERENCE,
			PT_complex, "I[A]", PADDR(I), PT_ACCESS, PA_REFERENCE,
			PT_complex, "P[VA]", PADDR(P), PT_ACCESS, PA_REFERENCE,
			NULL) < 1 )
		{
			GL_THROW("unable to publish properties in %s",__FILE__);
		}

		defaults = this;

		weather = NULL;
		temperature = humidity = solar = wind = rain = NULL;
		Theat = 60.0;
		Tcool = 70.0;
		memset((void*)imped_p,0,sizeof(imped_p));
		memset((void*)imped_q,0,sizeof(imped_q));
		memset((void*)current_p,0,sizeof(current_p));
		memset((void*)current_q,0,sizeof(current_q));
		memset((void*)power_p,0,sizeof(power_p));
		memset((void*)power_q,0,sizeof(power_q));
		memset((void*)input,0,sizeof(input));
		input[5] = 1.0; /* constant term */
		memset((void*)output,0,sizeof(output));
		Z = I = P = 0.0;

		strcpy(schedule, "* * * 1.0");
		load_class = LC_UNKNOWN;
    }
}

int triplex_zipload::create(void)
{
	int res = 0;
	
	memcpy((void*)this, defaults, sizeof(triplex_zipload));

	res = node::create();

    return res;
}

int triplex_zipload::isa(char *classname)
{
	return strcmp(classname,"triplex_zipload")==0 || triplex_load::isa(classname);
}

int triplex_zipload::init(OBJECT *parent)
{
	int rv = 0;
	int w_rv = 0;

	link_weather();

	build_schedule();

	if ( load_class != LC_UNKNOWN && strcmp(load_type,"") != 0 )
	{
		read_loadtype();
	}

	rv = triplex_load::init(parent);

	return w_rv ? 0 : rv;
}

TIMESTAMP triplex_zipload::precommit(TIMESTAMP t0)
{
	if ( temperature != NULL ) 
	{
		double T = *gl_get_double(weather, temperature);
		input[0] = T < Theat ? Theat - T : 0.0;
		input[1] = T > Tcool ? T - Tcool : 0.0;
	} 
	if ( solar != NULL ) 
	{
		input[2] = *gl_get_double(weather, solar);
	} 
	if ( wind != NULL ) 
	{
		input[3] = *gl_get_double(weather, wind);
	} 
	if ( rain != NULL )
	{
		input[4] = *gl_get_double(weather, rain);
	} 
	return TS_NEVER;
}

TIMESTAMP triplex_zipload::presync(TIMESTAMP t0)
{
	return triplex_load::presync(t0);
}

TIMESTAMP triplex_zipload::sync(TIMESTAMP t0)
{
	memset(output,0,sizeof(output));
	for ( unsigned int i = 0 ; i < sizeof(input)/sizeof(input[0]) ; ++i )
	{
		if ( input[i] != 0 )
		{
			output[0] += imped_p[i] * input[i];
			output[1] += imped_q[i] * input[i];
			output[2] += current_p[i] * input[i];
			output[3] += current_q[i] * input[i];
			output[4] += power_p[i] * input[i];
			output[5] += power_q[i] * input[i];
		}
	}

	// get schedule scalar
	if ( now != t0 )
	{	// update schedule cache
		gld_clock dt(t0);
		hour = dt.get_hour();
		weekday = dt.get_weekday();
		month = dt.get_month()-1;
		now = t0;
	}
	double scalar = scale[month][weekday][hour];

	Z = complex(output[0],output[1]) * scalar;
	I = complex(output[2],output[3]) * scalar;
	P = complex(output[4],output[5]) * scalar;

	double Zmag = Z.Mag();
	double Imag = I.Mag();
	double Pmag = P.Mag();
	double Smag = Zmag + Imag + Pmag;

	base_power[0] = base_power[1] = 0.0;
	base_power[2] = Smag;

	impedance_fraction[0] = impedance_fraction[1] = 0.0;
	impedance_fraction[2] = Zmag / Smag;
	current_fraction[0] = current_fraction[1] = 0.0;
	current_fraction[2] = Imag / Smag;
	power_fraction[0] = power_fraction[1] = 0.0;
	power_fraction[2] = Pmag / Smag;

	impedance_pf[0] = impedance_pf[1] = 0.0;
	impedance_pf[2] = ( Z.i > 0 ? 1 : -1 ) * Z.r/Zmag;
	current_pf[0] = current_pf[1] = 0.0;
	current_pf[2] = ( I.i > 0 ? 1 : -1 ) * I.r/Imag;
	power_pf[0] = power_pf[1] = 0.0;
	power_pf[2] = ( P.i > 0 ? 1 : -1 ) * P.r/Pmag;

	return triplex_load::sync(t0);
}

static unsigned int read_schedule(const char *str,unsigned int last=0)
{
	// fprintf(stderr,"read_schedule(const char *str='%s',unsigned int last=%u)\n",str,last);
	char *next=NULL, *prev=NULL;
	char buffer[strlen(str)+1];
	strcpy(buffer,str);
	while ( (next=strtok_r(next?NULL:buffer,",",&prev)) != NULL )
	{
		// fprintf(stderr,"  processing '%s'...\n",next);
		unsigned int from, to, value;
		if ( strchr(next,'-') != NULL )
		{
			if ( sscanf(next,"%u-%u",&from,&to) != 2 )
			{
				gl_error("schedule '%s' is not valid (hyphen found without from/to value)");
				return 0;
			}
			if ( from <= to && from <= last+1 && last < to )
			{
				// fprintf(stderr," --> %u\n",last+1);
				return last+1;
			}
			else if ( to < from && ( last < from || last+1 >= to ) )
			{
				// fprintf(stderr," --> %u\n",last+1);
				return last+1;
			}
			continue;
		}
		char *end = NULL;
		value = strtoul(next,&end,10);
		if ( *end != '\0' )
		{
			gl_error("schedule '%s' is not valid (invalid character after '%u'",next,value);
			return 0;
		}
		if ( value > last )
		{
			// fprintf(stderr," --> %u\n",value);
			return value;
		}
	}
	// fprintf(stderr," --> 0\n");
	return 0;
}

bool triplex_zipload::build_schedule(void)
{
	memset(scale,0,sizeof(scale)/sizeof(scale[0][0][0]));
	char *next=NULL, *last=NULL;
	char buffer[strlen((const char *)schedule)+1]; strcpy(buffer,(const char*)schedule);
	while ( (next=strtok_r(next?NULL:buffer,";",&last)) != NULL )
	{
		char months[256],days[256],hours[256],remark[256];
		double value;
		if ( sscanf(next,"%255[-0-9,*] %255[-0-9,*] %255[-0-9,*] %lg %[^\n]",
			months,days,hours,&value,remark) < 4 )
		{
			gl_error("schedule '%s' is not valid",next);
			return FALSE;
		}
		if ( strcmp(months,"*") == 0 )
		{
			strcpy(months,"1-12");
		}
		if ( strcmp(days,"*") == 0 )
		{
			strcpy(days,"1-8");
		}
		if ( strcmp(hours,"*") == 0 )
		{
			strcpy(hours,"1-24");
		}
		unsigned int hour = 0, day = 0, month = 0;
		// fprintf(stderr,"Schedule [%s]: months=[%s], days=[%s], hours=[%s], value=%lf, remark='%s'\n",
		// 	(const char*)schedule,months,days,hours,value,remark);
		while ( (hour=read_schedule(hours,hour)) > 0 )
		{
			if ( hour < 1 || hour > 24 )
			{
				gl_error("invalid hour in schedule '%s'",next);
				return FALSE;
			}
			while ( (day=read_schedule(days,day)) > 0 )
			{
			if ( day < 1 || day > 8 )
			{
				gl_error("invalid day in schedule '%s'",next);
				return FALSE;
			}
				while ( (month=read_schedule(months,month)) > 0 )
				{
				if ( month < 1 || month > 12 )
				{
					gl_error("invalid month in schedule '%s'",next);
					return FALSE;
				}
					scale[month-1][day-1][hour-1] = value;
				}
			}
		}
	}
	return TRUE;
}

void triplex_zipload::read_loadtype(void)
{
	// locate the file
	char pathname[1024];
	if ( gl_findfile(loaddata_pathname,NULL,R_OK,pathname,sizeof(pathname)-1) == NULL )
	{
		gl_error("unable to find '%s'",(const char*)loaddata_pathname);
		return;
	}

	// get the size of the file's contents
	struct stat buf;
	if ( stat(pathname,&buf) == -1 )
	{
		gl_error("unable to get size of '%s'",(const char*)pathname);		
		return;
	}
	load_data = (char*)malloc(buf.st_size+1);

	// open the file for reading	
	FILE *fp = fopen(pathname,"rb");
	if ( fp == NULL )
	{
		gl_error("unable to open '%s'",(const char*)pathname);
		return;
	}

	// read the file into the data buffer
	if ( fread((void*)load_data,1,buf.st_size,fp) < (unsigned int)buf.st_size )
	{
		gl_error("unable to read '%s'",(const char*)pathname);
		return;
	}
}

void triplex_zipload::link_weather(void)
{

	// old check
	if ( weather != NULL )
	{
		temperature = gl_get_property(weather, temperature_name);
		if ( temperature == NULL ) 
		{
			gl_error("unable to find '%s' property in weather object",(const char*)temperature_name);
		}
		
		humidity = gl_get_property(weather, humidity_name);
		if ( humidity == NULL ) 
		{
			gl_error("unable to find '%s' property in weather object",(const char*)humidity_name);
		}

		solar = gl_get_property(weather, solar_name);
		if ( solar == NULL )
		{
			gl_error("unable to find '%s' property in weather object",(const char*)solar_name);
		}

		wind = gl_get_property(weather, wind_name);
		if ( wind == NULL ) 
		{
			gl_error("unable to find '%s' property in weather object",(const char*)wind_name);
		}

		rain = gl_get_property(weather, rain_name);
		if ( rain == NULL ) 
		{
			gl_error("unable to find '%s' property in weather object",(const char*)rain_name);
		}
	}
}
