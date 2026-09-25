import sys, pandas, numpy;

data = pandas.read_csv("test_random_correlation.csv")
cov = numpy.cov(m=data.x,y=data.y)
s1,s12,s2,err = 0.975,-0.878,0.800,0.004
maxerr = numpy.max(numpy.abs([[s1,s12],[s12,s2]]-cov))
if maxerr > err :
	print(sys.argv[0],": covariance error (%g) is too large, cov = %s"%(maxerr,cov.flatten()))
	quit(1)

# test_random_correlation.csv test_random_correlation.png ''
data.plot(x='x',y='y',style=".",grid=True).get_figure().savefig("test_random_correlation.png")
