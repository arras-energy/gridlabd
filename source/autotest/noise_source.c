/* automatically generated code
Source: /Users/david/GitHub/arras-energy/gridlabd/source/autotest/test_external_null_source.glm(9)
 */
typedef struct { void *data, *info;} GLXDATA;
#define GLXdouble(X) (*((double*)(X.data)))

#line 9 "/Users/david/GitHub/arras-energy/gridlabd/source/autotest/test_external_null_source.glm"
double cos(double), sin(double);
	int noise(int nlhs, GLXDATA *plhs, int nrhs, GLXDATA *prhs)
	{	/* make sure the correct number of args are passed in */
		if ( nlhs!=1 || nlhs!=1 ) return -1;
		double t = GLXdouble(prhs[0]);
		GLXdouble(plhs[0]) = 1e6
		
			
			+ 4e5*cos(2*3.1416/86400*t)
			- 3e5*sin(2*2*3.1415/86400*t)
			
			
			+ 1.5e4*sin(57*3.1416/86400*t)
			- 1.9e4*sin(67*3.1416/86400*t)
			+ 1.7e4*sin(93*3.1416/86400*t)
			
			
			+ 1.3e3*sin(357*3.1416/86400*t)			
			- 1.5e3*sin(567*3.1416/86400*t)
			+ 1.9e3*sin(793*3.1416/86400*t)
			
			
			+ 1.9e2*sin(5357*3.1416/86400*t)
			- 1.3e2*sin(3567*3.1416/86400*t)
			+ 1.7e2*sin(9793*3.1416/86400*t);
		return 0;
	}	
