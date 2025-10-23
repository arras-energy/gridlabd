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
				PT_DESCRIPTION, "load type for zipload load parameter look-up",
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
			PT_double, "scalar[pu.W]", PADDR(scalar),
			PT_double, "H[degF]", PADDR(input[0]), PT_ACCESS, PA_REFERENCE,
			PT_double, "C[degF]", PADDR(input[1]), PT_ACCESS, PA_REFERENCE,
			PT_double, "S[kW]", PADDR(input[2]), PT_ACCESS, PA_REFERENCE,
			PT_double, "W[mph]", PADDR(input[3]), PT_ACCESS, PA_REFERENCE,
			PT_double, "R[in/h]", PADDR(input[4]), PT_ACCESS, PA_REFERENCE,
			PT_complex, "Z[ohm]", PADDR(Z), PT_ACCESS, PA_REFERENCE,
			PT_complex, "I[A]", PADDR(I), PT_ACCESS, PA_REFERENCE,
			PT_complex, "P[VA]", PADDR(P), PT_ACCESS, PA_REFERENCE,
			PT_char1024, "schedule", PADDR(schedule),
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
		scalar = 1.0;
		input[5] = 1.0; /* constant term */
		memset((void*)output,0,sizeof(output));
		Z = I = P = 0.0;
		strcpy(schedule, "* * * 1.0;");
		load_class = LC_UNKNOWN;
	}
}

int triplex_zipload::create(void)
{
	int res = 0;
	
	memcpy((void*)this, defaults, sizeof(triplex_zipload));
	service_status = ND_IN_SERVICE;
	bustype = PQ;

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
	double schedule_scale = scale[month][weekday][hour] / sqrt(3);

	Z = complex(output[0],output[1]) * schedule_scale * scalar;
	I = complex(output[2],output[3]) * schedule_scale * scalar;
	P = complex(output[4],output[5]) * schedule_scale * scalar;

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

void triplex_zipload::read_loadtype(void)
{
	get_load_data();

	char ndx[2048];
	char geocode[16] = "";
	if ( geocode_find >= 0 )
	{
		for ( OBJECT *obj = my() ; obj != NULL ; obj = obj->parent )
		{
			gld_object *object = get_object(obj);
			if ( isfinite(object->get_latitude()) && isfinite(object->get_longitude()) )
			{
				callback->geocode.encode(geocode,sizeof(geocode)-1,object->get_latitude(),object->get_longitude(),geocode_find>0?geocode_find:12);
				break;
			}
		}
		if ( geocode_find == 0 )
		{
			strcpy(geocode,find_nearest(geocode).c_str());
		}
		else if ( geocodes->find(geocode) == geocodes->end() )
		{
			gl_warning("geocode [%s] not found in %s, using default load data for null geocode",geocode,(const char*)loaddata_pathname);
			strcpy(geocode,"");
		}
	}

	gld_property load_class_property(my(),"load_class");
	gld_string load_class_string = load_class_property.get_string();
	snprintf(ndx,sizeof(ndx)-1,"%*s|%s|%s",geocode_find>0?geocode_find:12,geocode,(const char*)load_class_string,(const char*)load_type);
	table::ROW &data = load_data->at(ndx);

	Theat = data[load_data->column_index["Theat"]].to_double(0);
	Tcool = data[load_data->column_index["Tcool"]].to_double(0);

	imped_p[0] = data[load_data->column_index["Pz_H"]].to_double(0);
	imped_p[1] = data[load_data->column_index["Pz_C"]].to_double(0);
	imped_p[2] = data[load_data->column_index["Pz_S"]].to_double(0);
	imped_p[3] = data[load_data->column_index["Pz_W"]].to_double(0);
	imped_p[4] = data[load_data->column_index["Pz_R"]].to_double(0);
	imped_p[5] = data[load_data->column_index["Pz"]].to_double(0);

	imped_q[0] = data[load_data->column_index["Qz_H"]].to_double(0);
	imped_q[1] = data[load_data->column_index["Qz_C"]].to_double(0);
	imped_q[2] = data[load_data->column_index["Qz_S"]].to_double(0);
	imped_q[3] = data[load_data->column_index["Qz_W"]].to_double(0);
	imped_q[4] = data[load_data->column_index["Qz_R"]].to_double(0);
	imped_q[5] = data[load_data->column_index["Qz"]].to_double(0);

	current_p[0] = data[load_data->column_index["Pi_H"]].to_double(0);
	current_p[1] = data[load_data->column_index["Pi_C"]].to_double(0);
	current_p[2] = data[load_data->column_index["Pi_S"]].to_double(0);
	current_p[3] = data[load_data->column_index["Pi_W"]].to_double(0);
	current_p[4] = data[load_data->column_index["Pi_R"]].to_double(0);
	current_p[5] = data[load_data->column_index["Pi"]].to_double(0);

	current_q[0] = data[load_data->column_index["Qi_H"]].to_double(0);
	current_q[1] = data[load_data->column_index["Qi_C"]].to_double(0);
	current_q[2] = data[load_data->column_index["Qi_S"]].to_double(0);
	current_q[3] = data[load_data->column_index["Qi_W"]].to_double(0);
	current_q[4] = data[load_data->column_index["Qi_R"]].to_double(0);
	current_q[5] = data[load_data->column_index["Qi"]].to_double(0);

	power_p[0] = data[load_data->column_index["Pp_H"]].to_double(0);
	power_p[1] = data[load_data->column_index["Pp_C"]].to_double(0);
	power_p[2] = data[load_data->column_index["Pp_S"]].to_double(0);
	power_p[3] = data[load_data->column_index["Pp_W"]].to_double(0);
	power_p[4] = data[load_data->column_index["Pp_R"]].to_double(0);
	power_p[5] = data[load_data->column_index["Pp"]].to_double(0);

	power_q[0] = data[load_data->column_index["Qp_H"]].to_double(0);
	power_q[1] = data[load_data->column_index["Qp_C"]].to_double(0);
	power_q[2] = data[load_data->column_index["Qp_S"]].to_double(0);
	power_q[3] = data[load_data->column_index["Qp_W"]].to_double(0);
	power_q[4] = data[load_data->column_index["Qp_R"]].to_double(0);
	power_q[5] = data[load_data->column_index["Qp"]].to_double(0);

	strncpy(schedule,data[load_data->column_index["schedule"]].to_string().c_str(),sizeof(schedule)-1);
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
