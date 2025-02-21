// module/tape/multiplayer.h

#ifndef _G_MULTIPLAYER_H
#define _G_MULTIPLAYER_H

#include "gridlabd.h"

DECL_METHOD(multiplayer,file);
DECL_METHOD(multiplayer,property);

class multiplayer : public gld_object {

public:

	// keyword values
	typedef enum {MS_INIT=0, MS_OK=1, MS_DONE=2, MS_ERROR=3} MULTIPLAYERSTATUS;
	typedef enum {ERR_IGNORE=0, ERR_WARN=1, ERR_STOP=2} ONERROR;

public:

	// properties
	GL_ATOMIC(enumeration,status); 
	GL_ATOMIC(char32,indexname);
	GL_ATOMIC(enumeration,on_error);
	GL_METHOD(multiplayer,file);
	GL_METHOD(multiplayer,property);

private:

	// internal data
	char *fname;
	FILE *fp;
	char *line;
	size_t maxlen;
	TIMESTAMP next_t;
	std::list<gld_property> *target_list;
	std::list<double> *convert_list;
	std::string *property_list;

private:

	bool load(void);
	bool read(void);
	bool update(void);
	bool advance(TIMESTAMP t);

public:
	// required implementations 
	multiplayer(MODULE *module);
	int create(void);
	int init(OBJECT *parent);
	TIMESTAMP precommit(TIMESTAMP t1);
	TIMESTAMP presync(TIMESTAMP t1);
	TIMESTAMP sync(TIMESTAMP t1);
	TIMESTAMP postsync(TIMESTAMP t1);
	
public:

	static CLASS *oclass;
	static multiplayer *defaults;
};

#endif // _ASSERT_H
