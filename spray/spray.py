#!/usr/bin/env python
#
# v1.1.2
# SCRMacro for FIRE_WM v2017
# author: C. Schmalhorst
# (C) AVL Deutschland GmbH
# @date=20170322
# @version=112
#
import math
import numpy as np
import os

def intx(x, power):
    if power == 0: return x
    if power ==-1: return math.log(x)
    return x**(power+1)/(power+1)

def intx2(x, power):
    if power==0: return x
    if power==-1: return np.log(x)
    return x**(power+1.)/(power+1.)


def loadParticlesSizes(fname):
    d = []
    p = []
    if os.path.exists(fname):
        header = 0
        fp = open(fname)
        for line in fp:
            line = line.partition('#')[0]
            line = line.strip()
            if fname.endswith('.gid') and header < 10:
                if 'BEGIN' in line: header = 1
                if 'CHANNEL' in line: pass
                if 'UNIT' in line:
                    pass
                if'END' in line: header = 10
            else:
                vals = line.split()
#                print vals
                if len(vals)>1:
                    d.append( float(vals[0]) )
                    p.append( float(vals[1]) )
    return d,p

class Distribution:

    def __init__(self, diameters, probabilities):
        self.xvals = np.asarray(diameters)
        self.pvals = np.asarray(probabilities)
        self.numberweighted = True

#     public class FireTable
#     {
#         public List<xypoint> points;
#         public bool numberweighted;
#         public FireTable()
#         {
#         }
#         public FireTable(MalvernTable malvern)
#         {
#             this.numberweighted = malvern.numberweighted;
#             this.points = new List<xypoint>();
#             for (int i = 0; i < malvern.points.Count; i++)
#             {
#                 double x1 = malvern.points[i].d2 - 1E-12;
#                 double x2 = malvern.points[i].d2 + 1E-12;
#                 double f1 = malvern.pdf(x1);
#                 double f2 = malvern.pdf(x2);
#
#                 points.Add(new xypoint(x1, f1));
#                 points.Add(new xypoint(x2, f2));
#             }
#             this.points.Sort(delegate(xypoint c1, xypoint c2) { return c1.x.CompareTo(c2.x); });
#             double scaling = 1.0;
#             scaling = 1.0 / this.cpdf(this.getUpperLimit());
#             for (int i = 0; i < this.points.Count; i++)
#             {
#                 this.points[i].y *= scaling;
#             }
#         }
#         public FireTable(bool numberweighted, List<xypoint> xypoints)
#         {
#             this.numberweighted = numberweighted;
#             this.points = new List<xypoint>(xypoints);
#             this.points.Sort(delegate(xypoint c1, xypoint c2) { return c1.x.CompareTo(c2.x); });
#
#             double scaling = 1.0;
#             scaling = 1.0 / this.intprob(this.getUpperLimit(), 0);
#             for (int i = 0; i < this.points.Count; i++)
#             {
#                 this.points[i].y *= scaling;
#             }
#         }

    def getUpperLimit(self):
        return np.max(self.xvals)

    def getLowerLimit(self):
        return np.min(self.pvals)

    def pdf(self, x):
        """
        Get value of probability density for d=x.
        Does linear interpolation. If x is not within table range, pdf(x) will return 0
        """
        if len(self.xvals) == 0 :
            return 0
        if x < np.min(self.xvals) or x > np.max(self.xvals):
            return 0
        return np.interp(x, self.xvals, self.pvals)

        #return self.pvals[i-1] + (self.pvals[i] - self.pvals[i-1]) * (x-self.xvals[i-1])/(self.xvals[i]-self.xvals[i-1])

#         public double pdf(double x)
#         {
#             if (this.points.Count == 0) return 0.0;
#             double prob = 0.0;
#             for (int i = 0; i < this.points.Count - 1; i++)
#             {
#                 if (this.points[i + 1].x >= x && this.points[i].x <= x)
#                 {
#                     double d1 = this.points[i].x;
#                     double d2 = this.points[i + 1].x;
#                     double p1 = this.points[i].y;
#                     double p2 = this.points[i + 1].y;
#                     double fac = (x - d1) / (d2 - d1);
#                     prob = fac * (p2 - p1) + p1;
#                     return prob;
#                 }
#             }
#             return 0.0;
#         }

    def cpdf(self, x):
        """
        Get value of cumulative probability for d=x
        Does linear interpolation. Trapez rule will be used for integration.
        """
        if len(self.xvals) == 0:
            return 0

        i = np.searchsorted(self.xvals, x)

        if i == 0: return 0
        if i == len(self.xvals): return 1

        _x = np.hstack( ( self.xvals[:i] , (x,) )  )
        _y = np.hstack(  (self.pvals[:i], (self.pdf(x),) ) )

        #_x.append(x)
        #_y.append(self.pdf(x))


        return np.trapz(_y, x=_x)
#
#         public double cpdf(double x)
#         {
#             if (this.points.Count == 0) return 0.0;
#             double cprob_sum = 0.0;
#             for (int i = 0; i < this.points.Count - 1; i++)
#             {
#                 double d1 = this.points[i].x;
#                 double d2 = this.points[i + 1].x;
#                 double p1 = this.points[i].y;
#                 double p2 = this.points[i + 1].y;
#                 if (this.points[i + 1].x >= x && this.points[i].x <= x)
#                 {
#                     double dx = x - d1;
#                     double fac = dx / (d2 - d1);
#                     double prob = fac * (p2 - p1) + p1;
#                     cprob_sum += 0.5 * (prob + p1) * dx;
#                     return cprob_sum;
#                 }
#                 double cprob = (p2 + p1);
#                 cprob *= 0.5 * (d2 - d1);
#                 cprob_sum += cprob;
#             }
#             return cprob_sum;
#         }
#         public double getUpperLimit()
#         {
#             if (this.points.Count == 0) return 0.0;
#             double maxval = -this.points[0].x;
#             for (int i = 0; i < this.points.Count; i++)
#             {
#                 if (this.points[i].x > maxval)
#                 {
#                     maxval = this.points[i].x;
#                 }
#             }
#             if (maxval > 0) return maxval;
#             return maxval;
#         }
#         public double getLowerLimit()
#         {
#             if (this.points.Count == 0) return 0.0;
#             double minval = this.points[0].x;
#             for (int i = 0; i < this.points.Count; i++)
#             {
#                 if (this.points[i].x < minval)
#                 {
#                     minval = this.points[i].x;
#                 }
#             }
#             if (minval > 0) return minval;
#             return minval;
#         }

#
#         public double intx(double x, int power)
#         {
#             if (power > 0)
#             {
#                 return Math.Pow(x, power + 1) / (power + 1);
#             }
#             else if (power == 0)
#             {
#                 return x;
#             }
#             else if (power == -1)
#             {
#                 return Math.Log(x);
#             }
#             else if (power < -1)
#             {
#                 return Math.Pow(x, power + 1) / (power + 1);
#             }
#             return 0;
#         }


    def intprob2(self, x_in, x_power):
        """Integral probability of particle size distribution.
        x_in:     droplet size
        x_power:
        """
        if len(self.xvals) == 0: return ( 0, )
        i = np.searchsorted(self.xvals, x_in)
        if i == 0: return ( 0, )
        if i == len(self.xvals):
            i -= 1

        xslice = np.hstack( ( self.xvals[:i], [x_in,]) )
        yslice = self.pvals[:i+1]

        a = np.asarray(xslice[:-1])
        b = np.asarray(xslice[1:])
        fa = np.asarray(yslice[:-1])
        fb = np.asarray(yslice[1:])
        k = (fb - fa) / (b-a) # Steigung in allen Punkten!
        d = fa - k * a

        #pow1 = np.copy(xslice)
        #pow0 = np.copy(xslice)
        #def fpow1(x):
        #    return intx(x, x_power+1)
        #def fpow(x):
        #    return intx(x, x_power)
        #pow1 = np.apply_along_axis(fpow1, 0, pow1)
        #pow0 = np.apply_along_axis(fpow, 0, pow0)

        pow1 = intx2(xslice, x_power+1.)
        pow0 = intx2(xslice, x_power)

        return np.cumsum( (k * pow1[1:] + d * pow0[1:] - k* pow1[:-1] - d*pow0[:-1]), 0)

    def intprob(self, x_in, x_power):
        return self.intprob2(x_in, x_power)[-1]

#         public double intprob(double xin, int xpower)
#         {
#             if (this.points.Count == 0) return 0;
#             if (this.points[0].x > xin) return 0;
#             double sum = 0;
#
#                 for (int i = 0; i < this.points.Count - 1; i++)
#                 {
#                     if (xin >= this.points[i].x && xin < this.points[i + 1].x)
#                     {
#                         double a = this.points[i].x;
#                         double b = this.points[i + 1].x;
#                         double fa = this.points[i].y;
#                         double fb = this.points[i + 1].y;
#                         double k = (fb - fa) / (b - a);
#                         double d = fa - k * a;
#                         double inta = k * intx(a, xpower + 1) + d * intx(a, xpower);
#                         double intb = k * intx(xin, xpower + 1) + d * intx(xin, xpower);
#                         sum += (intb - inta);
#                         return sum;
#                     }
#                     {
#                         double a = this.points[i].x;
#                         double b = this.points[i + 1].x;
#                         if (b - a < 2E-12) continue;
#                         double fa = this.points[i].y;
#                         double fb = this.points[i + 1].y;
#                         double k = (fb - fa) / (b - a);
#                         double d = fa - k * a;
#                         double inta = k * intx(a, xpower + 1) + d * intx(a, xpower);
#                         double intb = k * intx(b, xpower + 1) + d * intx(b, xpower);
#                         sum += (intb - inta);
#                     }
#                 }
#                 return sum;
#         }

    def getDXY(self, x,y):
        u = self.getUpperLimit()
        sumx = self.intprob(u,x)
        sumy = self.intprob(u,y)
        return sumx / sumy


    def getD32(self):
        if self.numberweighted:
            return self.getDXY(3,2)
        else:
            return self.getDXY(-1,0)

#         public double getd32()
#         {
#             if (this.numberweighted)
#             {
#                 double u = this.getUpperLimit();
#                 double sum2 = this.intprob(u, 2);
#                 double sum3 = this.intprob(u, 3);
#                 return sum3 / sum2;
#             }
#             else
#             {
#                 double u = this.getUpperLimit();
#                 double sum2 = this.intprob(u, -1);
#                 double sum3 = this.intprob(u, 0);
#                 return sum3 / sum2;
#             }
#         }
    def getD43(self):
        if self.numberweighted:
            return self.getDXY(4,3)
        else:
            return self.getDXY(1,0)
#         public double getd43()
#         {
#             if (this.numberweighted)
#             {
#                 double u = this.getUpperLimit();
#                 double sum4 = this.intprob(u, 4);
#                 double sum3 = this.intprob(u, 3);
#                 return sum4 / sum3;
#             }
#             else
#             {
#                 double u = this.getUpperLimit();
#                 double sum4 = this.intprob(u, 1);
#                 double sum3 = this.intprob(u, 0);
#                 return sum4 / sum3;
#             }
#         }

    def getD10(self):
        if self.numberweighted:
            return self.getDXY(1,0)
        else:
            return self.getDXY(-2,-3)
#         public double getd10()
#         {
#             if (this.numberweighted)
#             {
#                 double u = this.getUpperLimit();
#                 double sum1 = this.intprob(u, 1);
#                 double sum0 = this.intprob(u, 0);
#                 return sum1 / sum0;
#             }
#             else
#             {
#                 double u = this.getUpperLimit();
#                 double sum1 = this.intprob(u, -2);
#                 double sum0 = this.intprob(u, -3);
#                 return sum1 / sum0;
#             }
#         }
    def getD30(self):
        if self.numberweighted:
            return self.getDXY(3,0)**(1./3.)
        else:
            return self.getDXY(0,-3)**(1./3.)
#         public double getd30()
#         {
#             if (this.numberweighted)
#             {
#                 double u = this.getUpperLimit();
#                 double sum3 = this.intprob(u, 3);
#                 double sum0 = this.intprob(u, 0);
#                 return Math.Pow(sum3 / sum0, 1.0 / 3.0);
#             }
#             else
#             {
#                 double u = this.getUpperLimit();
#                 double sum3 = this.intprob(u, 0);
#                 double sum0 = this.intprob(u, -3);
#                 return Math.Pow(sum3 / sum0, 1.0/3.0);
#             }
#         }

    def getDNX0(self, nfac, index):
        if len(self.xvals)==0:
            return 0

        def func(x):
            return self.intprob(x, index)

        sums = np.hstack(  (0, self.intprob2(self.xvals[-1], index)))

#        sums = map(func, self.xvals)
#        sums = np.asarray(sums)
        i = np.searchsorted(sums, nfac)

        if i == 0: return 0
        if i == len(sums): return np.max(self.xvals)
        print i
        return np.interp( nfac, sums, self.xvals )

        #iterative search for intprob(x) = nfac
#        u = self.xvals[i]
#        l = self.xvals[i-1]
#        j = 0
#        ITERMAX = 1e4
#        while True:
#            j += j
#            if j>ITERMAX:
#                return 0

#            n = (u+l)*.5
#            if 0.5*abs( u - l )/abs(u+l) < 1e-6: return n

#            nc = self.intprob(n, index)

#            if nfac > nc:
#                l = n
#            else:
#                u = n

    def getDNX(self, fac):
        if not self.numberweighted:
            index = -3
            fac *= self.intprob(max(self.xvals), index)

        else:
            index = 0
        return self.getDNX0(fac,index)

    def getDVX(self, fac):
        if self.numberweighted:
            index = 3
            fac *= self.intprob(self.getUpperLimit(), index)
        else:
            index = 0
        return self.getDNX0(fac,index)

#         public double getdnx0(double nfac)
#         {
#             int nitermax = 10000;
#             int index = 0;
#             if (!this.numberweighted)
#             {
#                 index = -3;
#                 nfac *= this.intprob(this.getUpperLimit(), index);
#             }
#             if (this.points.Count == 0) return 0.0;
#             for (int i = 0; i < this.points.Count - 1; i++)
#             {
#                 double fac = nfac;
#                 double d1 = this.points[i].x;
#                 double d2 = this.points[i + 1].x;
#                 double sum1 = this.intprob(d1, index);
#                 double sum2 = this.intprob(d2, index);
#                 if (sum2 > nfac && nfac >= sum1)
#                 {
#                     int j = 0;
#                     double u = d2;
#                     double l = d1;
#                     double cu = sum2;
#                     double cl = sum1;
#                     while (true)
#                     {
#                         double n = (u + l) * 0.5;
#                         double nc = this.intprob(n, index);
#                         if (nc >= nfac && nfac >= cl)
#                         {
#                             u = n;
#                             cu = nc;
#                         }
#                         else if (cu >= nfac && nfac > nc)
#                         {
#                             cl = nc;
#                             l = n;
#                         }
#                         if (0.5 * Math.Abs(u - l) / Math.Abs(u + l) < 1E-6)
#                         {
#                             return n;
#                         }
#                         if (nitermax < j) return 0;
#                         j++;
#                     }
#                 }
#             }
#             return 0.0;
#         }
    def getDN10(self):
        return self.getDNX(0.1)
    def getDN50(self):
        return self.getDNX(0.5)
    def getDN90(self):
        return self.getDNX(0.9)

    def getDV10(self):
        return self.getDVX(0.1)
    def getDV50(self):
        return self.getDVX(0.5)
    def getDV90(self):
        return self.getDVX(0.9)


#         public double getdn10()
#         {
#             return this.getdnx0(0.1);
#         }
#         public double getdn50()
#         {
#             return this.getdnx0(0.5);
#         }
#         public double getdn90()
#         {
#             return this.getdnx0(0.9);
#         }
#         public double getdvx0(double nfac)
#         {
#             int nitermax = 10000;
#             int index = 0;
#             if (this.numberweighted)
#             {
#                 index = 3;
#                 nfac *= this.intprob(this.getUpperLimit(), index);
#             }
#             if (this.points.Count == 0) return 0.0;
#             for (int i = 0; i < this.points.Count - 1; i++)
#             {
#                 double fac = nfac;
#                 double d1 = this.points[i].x;
#                 double d2 = this.points[i + 1].x;
#                 double sum1 = this.intprob(d1, index);
#                 double sum2 = this.intprob(d2, index);
#                 if (sum2 > nfac && nfac >= sum1)
#                 {
#                     int j = 0;
#                     double u = d2;
#                     double l = d1;
#                     double cu = sum2;
#                     double cl = sum1;
#                     while (true)
#                     {
#                         double n = (u + l) * 0.5;
#                         double nc = this.intprob(n, index);
#                         if (nc >= nfac && nfac >= cl)
#                         {
#                             u = n;
#                             cu = nc;
#                         }
#                         else if (cu >= nfac && nfac > nc)
#                         {
#                             cl = nc;
#                             l = n;
#                         }
#                         if (0.5 * Math.Abs(u - l) / Math.Abs(u + l) < 1E-6)
#                         {
#                             return n;
#                         }
#                         if (nitermax < j) return 0;
#                         j++;
#                     }
#                 }
#             }
#             return 0.0;
#         }
#         public double getdv10()
#         {
#             return this.getdvx0(0.1);
#         }
#         public double getdv50()
#         {
#             return this.getdvx0(0.5);
#         }
#         public double getdv90()
#         {
#             return this.getdvx0(0.9);
#         }
#         public FireTable convertToxypoint(bool numberweighted)
#         {
#             if (this.numberweighted == numberweighted)
#             {
#                 return this;
#             }
#             else
#             {
#                 List<xypoint> newpoints = new List<xypoint>();
#                 if (this.numberweighted)
#                 {
#                     for (int i = 0; i < this.points.Count; i++)
#                     {
#                         double x = this.points[i].x;
#                         double y = this.points[i].y * Math.Pow(x, 3.0);
#                         newpoints.Add(new xypoint(x, y));
#                     }
#                 }
#                 else
#                 {
#                     for (int i = 0; i < this.points.Count; i++)
#                     {
#                         double x = this.points[i].x;
#                         double y = this.points[i].y * Math.Pow(x, -3.0);
#                         newpoints.Add(new xypoint(x, y));
#                     }
#                 }
#                 return new FireTable(numberweighted, newpoints);
#             }
#         }
#         public StepfunctionTable convertToRangepoint(StepfunctionTable.WeightType weighttype,
#                                                      StepfunctionTable.StepType step,
#                                                      StepfunctionTable.IntegrationType inttype)
#         {
#             double referenced32 = this.getd32();
#             double reld32diff = 0.005;
#             double u = this.getUpperLimit();
#             double l = this.getLowerLimit();
#             int itermax = 1000;
#             List<rangepoint> newpoints = new List<rangepoint>();
#             for (int i = 1; i < itermax; i++)
#             {
#                 /*
#                 newpoints = new List<rangepoint>();
#                 iter = (this.points.Count - 1) * Math.Pow(2, i);
#                 double dx = (u - l) / iter;
#                 for (int j = 0; j < iter; j++)
#                 {
#                     double d1 = l + dx * j;
#                     double d2 = l + dx * j + dx;
#                     double prob = 0.0;
#                     if(weighttype == StepfunctionTable.WeightType.number && this.numberweighted)
#                     {
#                         double x = (d2 + d1)/2.0;
#                         prob = this.pdf(x);
#                     }
#                     else if(weighttype == StepfunctionTable.WeightType.number && !this.numberweighted)
#                     {
#                         double x = (d2 + d1)/2.0;
#                         prob = this.pdf(x)/Math.Pow(x,3.0);
#                     }
#                     else if (weighttype == StepfunctionTable.WeightType.volume && !this.numberweighted)
#                     {
#                         double x = (d2 + d1) / 2.0;
#                         prob = this.pdf(x);
#                     }
#                     else if (weighttype == StepfunctionTable.WeightType.volume && this.numberweighted)
#                     {
#                         double x = (d2 + d1) / 2.0;
#                         prob = this.pdf(x) * Math.Pow(x, 3.0);
#                     }
#                     if (step == StepfunctionTable.StepType.histogram)
#                     {
#                         prob *= (d2 - d1);
#                     }
#                     newpoints.Add(new rangepoint(d1,d2,prob));
#                 }
#                 */
#                 newpoints = new List<rangepoint>();
#                 for (int j = 0; j < this.points.Count-1; j++)
#                 {
#                     double ux = this.points[j + 1].x;
#                     double lx = this.points[j].x;
#                     double dx = (ux - lx) / i;
#                     for (int k = 0; k < i; k++)
#                     {
#                         double d1 = lx + dx * k;
#                         double d2 = lx + dx * k + dx;
#                         double prob = 0.0;
#                         if (weighttype == StepfunctionTable.WeightType.number && this.numberweighted)
#                         {
#                             double x = (d2 + d1) / 2.0;
#                             prob = this.pdf(x);
#                         }
#                         else if (weighttype == StepfunctionTable.WeightType.number && !this.numberweighted)
#                         {
#                             double x = (d2 + d1) / 2.0;
#                             prob = this.pdf(x) / Math.Pow(x, 3.0);
#                         }
#                         else if (weighttype == StepfunctionTable.WeightType.volume && !this.numberweighted)
#                         {
#                             double x = (d2 + d1) / 2.0;
#                             prob = this.pdf(x);
#                         }
#                         else if (weighttype == StepfunctionTable.WeightType.volume && this.numberweighted)
#                         {
#                             double x = (d2 + d1) / 2.0;
#                             prob = this.pdf(x) * Math.Pow(x, 3.0);
#                         }
#                         if (step == StepfunctionTable.StepType.histogram)
#                         {
#                             prob *= (d2 - d1);
#                         }
#                         newpoints.Add(new rangepoint(d1, d2, prob));
#                     }
#                 }
#                 StepfunctionTable sft_test = new StepfunctionTable(weighttype, step, inttype, newpoints);
#                 double d32_test = sft_test.getd32();
#                 if(Math.Abs(referenced32 - d32_test)/Math.Abs((referenced32 + d32_test)*0.5) < reld32diff)
#                 {
#                     return sft_test;
#                 }
#             }
#             return null;
#         }
#     }
