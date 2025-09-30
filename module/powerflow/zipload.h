// module/powerflow/zipload.h
// Copyright (C) 2025 Eudoxys Sciences LLC

#ifndef _ZIPLOAD_H
#define _ZIPLOAD_H

#ifndef _POWERFLOW_H
#error "this header must be included by powerflow.h"
#endif

table *get_load_data(void);
std::string find_nearest(const char *geocode);

class zipload : public load
{
public:

	// schedule cache
	static unsigned int hour;
	static unsigned int weekday;
	static unsigned int month;
	static TIMESTAMP now;

public:

	char1024 load_type; // see zipload.csv
	double Theat, Tcool; // heating and cooling balance temperatures
	double imped_p[6]; // Pz_{H,C,S,W,R,1}
	double imped_q[6]; // Qz_{H,C,S,W,R,1}
	double current_p[6]; // Pi_{H,C,S,W,R,1}
	double current_q[6]; // Qi_{H,C,S,W,R,1}
	double power_p[6]; // Pp_{H,C,S,W,R,1}
	double power_q[6]; // Qo_{H,C,S,W,R,1}
	double input[6]; // H, C, S, W, R, 1.0 */
	double output[6]; // Zp, Zq, Ip, Iq, Pp, Pq */
	complex Z[3], I[3], P[3]; // Zp+Zq*1j, Ip+Iq*1j, Pp+Pq*1j
	double scalar;
	
	char1024 schedule;
	double scale[12][8][24]; // month, weekday, hour

	OBJECT *weather;
	PROPERTY *temperature, *humidity, *solar, *wind, *rain;

	int create(void);

	bool build_schedule(void);
	void read_loadtype(void);
	void link_weather(void);

	zipload(MODULE *mod);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t0);
	TIMESTAMP presync(TIMESTAMP t0);
	TIMESTAMP sync(TIMESTAMP t0);
	int isa(char *classname);

public:

	static zipload *defaults;
	static CLASS *oclass;
	static CLASS *pclass;
	
};

#endif // _ZIPLOAD_H

