# Christopher Lee (c) 2000
# code commisioned by Greg Wilson 
# draw polynomial functions using bezier exact representations in piddle

# Primary Interface Functions:
#    drawQuad - draws to a canvas
#    drawCubicPolynomial
#    class CoordFrame  - defines a coordinate frame in which to draw
    
# See the function runtest() for basic use

# Testing:
#   works w/ piddlePS and piddlePIL

    

def quadratic(x,A,B,C):
    # y(x) = A x^2 + B x + C
    return A*x*x + B*x + C

def cubic(x, A,B,C,D):
    # y(x) = A x^3 + B x^2 + C x + D
    xsq = x * x
    return A * x * xsq + B * xsq + C * x + D


def quadPts(xinterval,  A=0., B=0., C=0.):
    """return the control points for a bezier curve that fits the quadratic function
    y = A x^2 + B x + C.  for the interval along the x-axis given by xinterval=(x0,x1)"""
    # y(x) = A x^2  + B x + C
    # for x \in [ xinterval[0], xinterval[1] ]
    x0 = float(xinterval[0])
    x3 = float(xinterval[1])
    y0 = quadratic(x0, A,B,C)
    ### print 'y0=', y0 DEBUG

    xlen = x3-x0
    # print 'xlen = ', xlen
    cx = xlen  # set x scaling, check if makes sense for xlen <0
    
    # convert to cubic paramaters, adjust for xscaling
    # lower case used for cubic: w(t) = a t^3 + b*t^2 + c* t + w0
    # t: [0,1]
    # parameters are adjusted to accout for x(t) = cx*t+x0 tranformation
    #by <-> A
    #cy <-> B
    a = (0,0)
    b = (0, A*cx*cx )
    c = (cx, B*cx+2*b[1]*x0/cx)
    v0 = (x0,C-(b[1]/(cx*cx)) *x0*x0) ;
    ### print a,b,c,v0
    x = [x0, 0, 0, 0]; y = [y0, 0, 0, 0]
    v = [x, y]
    for ii in (0, 1): # iterate over vector components 
        v[ii][1] = v[ii][0] + c[ii]/3.0
        v[ii][2] = v[ii][1] + (c[ii]+b[ii])/3.0
        v[ii][3] = v[ii][0] + c[ii] + b[ii] + a[ii]

    return (v[0][0], v[1][0],
            v[0][1], v[1][1],
            v[0][2], v[1][2],
            v[0][3], v[1][3])
    
def cubicPts(xinterval,  A=0., B=0., C=0., D=0):
    """return the control points for a bezier curve that fits the cubic polynomial
    y = A x^3 + B x^2 + C x + D.  for the interval along the x-axis given by
    xinterval=(xStart,xEnd)"""
    # for x \in [ xinterval[0], xinterval[1] ]
    x0 = float(xinterval[0])
    x3 = float(xinterval[1])
    y0 = cubic(x0, A,B,C,D)  # y0 = y(x0)
    # print 'y0=', y0 ##DEBUG

    xlen = x3-x0
    # print 'xlen = ', xlen
    cx = xlen  # set x scaling, check if makes sense for xlen <0
    
    # convert to cubic paramaters, adjust for xscaling
    # lower case used for cubic: w(t) = a t^3 + b*t^2 + c* t + w0
    # t: [0,1]
    # parameters are adjusted to accout for x(t) = cx*t+x0 tranformation
    #by <-> A
    #cy <-> B
    a = (0,A*cx*cx*cx) 
    b = (0, B*cx*cx+ 3*A*cx*cx*x0 )
    c = (cx, C*cx + 2*B*cx*x0+3*A*cx*x0*x0)
    v0 = (x0,y0) ;
    ### print a,b,c,v0
    x = [x0, 0, 0, 0]; y = [y0, 0, 0, 0]
    v = [x, y]
    for ii in (0, 1): # iterate over vector components 
        v[ii][1] = v[ii][0] + c[ii]/3.0
        v[ii][2] = v[ii][1] + (c[ii]+b[ii])/3.0
        v[ii][3] = v[ii][0] + c[ii] + b[ii] + a[ii]

    return (v[0][0], v[1][0],
            v[0][1], v[1][1],
            v[0][2], v[1][2],
            v[0][3], v[1][3])


class AffineMatrix:
    # taken from PyArt
    # use this for transforming vpaths and bpaths, can also be used to set gstate.CTM
    # A = [ a c e]
    #     [ b d f]
    #     [ 0 0 1]
    # self.A = [a b c d e f] = " [ A[0] A[1] A[2] A[3] A[4] A[5] ]"
    def __init__(self, init=None):
        if init:
            if len(init) == 6 :
                self.A = init
            if type(init) == type(self): # erpht!!! this seems so wrong
                self.A = init.A
        else:
            self.A = [1.0, 0, 0, 1.0, 0.0, 0.0] # set to identity

    def scale(self, sx, sy):
        self.A = [sx*self.A[0], sx*self.A[1], sy*self.A[2], sy * self.A[3], self.A[4], self.A[5] ]

    def rotate(self, theta):
        "counter clockwise rotation in standard SVG/libart coordinate system"
        # clockwise in postscript "y-upward" coordinate system
        # R = [ c  -s  0 ]
        #     [ s   c  0 ]
        #     [ 0   0  1 ]

        co = math.cos(PI*theta/180.0)
        si = math.sin(PI*theta/180.0)
        self.A = [self.A[0] * co + self.A[2] * si,
                  self.A[1] * co + self.A[3] * si,
                  -self.A[0]* si + self.A[2] * co,
                  -self.A[1]* si + self.A[3] * co,
                  self.A[4],
                  self.A[5] ]

    def translate(self, tx, ty):
        self.A  = [ self.A[0], self.A[1], self.A[2], self.A[3],
                    self.A[0]*tx + self.A[2]*ty + self.A[4],
                    self.A[1]*tx + self.A[3]*ty + self.A[5] ]

    def rightMultiply(self, a, b, c, d, e, f):
        "multiply self.A by matrix M defined by coefficients a,b,c,d,e,f"
        # 

        #             [    m0*a+m2*b,    m0*c+m2*d, m0*e+m2*f+m4]
        #  ctm * M =  [    m1*a+m3*b,    m1*c+m3*d, m1*e+m3*f+m5]
        #             [            0,            0,            1]
        m= self.A
        self.A = [ m[0]*a+m[2]*b,
                   m[1]*a+m[3]*b,
                   m[0]*c+m[2]*d,
                   m[1]*c+m[3]*d,
                   m[0]*e+m[2]*f+m[4],
                   m[1]*e+m[3]*f+m[5] ]

    def transformPt(self, pt):
        #                   [
        #  pt = A * [x, y, 1]^T  =  [a*x + c*y+e, b*x+d*y+f, 1]^T
        #
        x,y = pt
        a,b,c,d,e,f = self.A
        return [ a*x + c*y+e, b*x+d*y+f]
        
    def transformFlatList(self, seq):
        # transform a (flattened) sequence of points in form [x0,y0, x1,y1,..., x(N-1), y(N-1)]
        N = len(seq) # assert N even

        # would like to reshape the sequence, do w/ a loop for now
        res = []
        for ii in range(0,N, 2):
            pt = self.transformPt( (seq[ii], seq[ii+1]) )
            res.extend(pt)

        return res

#    def transformPath(self, path):  # overload multiply for this
#        # experiment w/ skipping intermediate call
#        Part2Libart.PartVpath_transform(path._Ppath, self.A)



class CoordFrame:
    # Essentially this identifies a target rectangle on the canvas
    # in which to draw and allows me to rescale the coordinates (u is for user coordinates)
    # within the box for my convenience when plotting
    # Note: no clipping is done
    def __init__(self,x0,y0, w, h, uX0, uY0, uWidth=1.0, uHeight=1.0, theta=0.0):
        self.x0 = x0
        self.y0 = y0
        self.w = w
        self.h = h
        # might want to save other parameters later

        Sx = float(w)/uWidth
        Sy = float(h)/uHeight
        
        self.u2dTM = AffineMatrix() # user to device transformation matrix

        self.u2dTM.translate(x0, y0)

        # if YaxisGoesUp
        self.u2dTM.translate(0,h) # go down this far
        self.u2dTM.scale(Sx, -Sy)  
        self.u2dTM.translate(-uX0, -uY0)  

    def drawFrameBox(self,canvas):
        'Draw a rectangle that represents the "target area" for the coord frame'
        # helps with debugging
        canvas.drawRect(self.x0, self.y0, self.x0+self.w, self.y0 + self.h)
        


def drawCircleAt(canvas, x,y,r, **kw):
    # useful for marking a particular location w/ a glyph
    df = canvas.__class__
    df.drawEllipse(*(canvas, x-r, y-r, x+r,y+r), **kw)


def drawCubicPolynomial(canvas, frame, xinterval, A=0.0, B=0.0, C=0.0, D=0.0,
             edgeColor=None, edgeWidth=None,fillColor=None):
    ctlpts = cubicPts(xinterval=xinterval, A=A,B=B,C=C, D=D)
    Tctlpts = frame.u2dTM.transformFlatList(ctlpts)
    canvas.drawCurve(Tctlpts[0],Tctlpts[1],Tctlpts[2],Tctlpts[3],
                     Tctlpts[4],Tctlpts[5],Tctlpts[6],Tctlpts[7],
                     edgeColor=edgeColor,edgeWidth=edgeWidth,
                     fillColor=fillColor)





def drawQuad(canvas, frame, xinterval, A=0.0, B=0.0, C=0.0,
             edgeColor=None, edgeWidth=None,fillColor=None):
    qpts = quadPts(xinterval=xinterval, A=A,B=B,C=C)
    Tqpts = frame.u2dTM.transformFlatList(qpts)
    canvas.drawCurve(Tqpts[0],Tqpts[1],Tqpts[2],Tqpts[3],
                     Tqpts[4],Tqpts[5],Tqpts[6],Tqpts[7], edgeColor=edgeColor,edgeWidth=edgeWidth,
                     fillColor=fillColor)


def drawQuadWithCtrlPts(canvas, frame, xinterval, A=0.0, B=0.0, C=0.0,
                        edgeColor=None, fillColor=None):
    # This is useful for debugging--shows where the bezier control points really are
    qpts = quadPts(xinterval=xinterval, A=A,B=B,C=C)
    Tqpts = frame.u2dTM.transformFlatList(qpts)
    canvas.drawCurve(Tqpts[0],Tqpts[1],Tqpts[2],Tqpts[3],
                     Tqpts[4],Tqpts[5],Tqpts[6],Tqpts[7])
    # useful code for marking ctrl pts
    drawCircleAt(canvas, Tqpts[0], Tqpts[1], 5)
    drawCircleAt(canvas, Tqpts[2], Tqpts[3], 5)
    drawCircleAt(canvas, Tqpts[4], Tqpts[5], 5)
    drawCircleAt(canvas, Tqpts[6], Tqpts[7], 5)
    

def runtest():
    # These are my parameters for the coodinate frame
    # Essentially this identifies a target rectangle on the canvas
    # in which to draw and allows me to rescale the coordinates
    # within the box for my convenience when plotting
    # Note: no clipping is done
    import sys,os, os.path
    sys.path.append(os.path.join(os.getcwd(), "examples"))
    import textClasses
    
    my_x0 = 50
    my_y0 = 50
    my_w  = 300
    my_h  = 300

    my_uX0 = -10.0
    my_uY0 = -100.0
    my_uWidth = 20.0
    my_uHeight = 200.0
    
    frame = CoordFrame(x0= my_x0, y0= my_y0, w=my_w, h=my_h,
                       uX0= my_uX0, uY0= my_uY0,
                       uWidth= my_uWidth,
                       uHeight= my_uHeight)

    import piddlePS

    canvas = piddlePS.PSCanvas((400,400), 'qtest.ps')


    def ToCanvas(canvas, frame, textClasses=textClasses):
        # Given a canvas and a coordinate frame, do some tests on it
        frame.drawFrameBox(canvas)
        # draw a family of quadratics w/in the box w/ x-intercept x=0
        NA = 10.0
        for AA in range(1,NA,2):
            drawQuad(canvas, frame, xinterval=(-10,10), A= AA/NA, B=0.0)
            
        # now some other assorted quadratics
        
        drawQuad(canvas, frame, xinterval=(-10,10), A=-1.0, B=0.0, C=0, edgeColor=piddle.red)
        # shift down and add B portion
        drawQuad(canvas, frame, xinterval=(-10,10), A=-.4, B=-3.0, C=-30.0, edgeColor=piddle.blue)

        drawCubicPolynomial(canvas, frame, xinterval=(-10,10), A=.14, B=-1.4, C=-10,D=85,
                                                      edgeColor=piddle.purple)


        textbox = textClasses.TextBox(canvas, 100,350, 200, 50, input_text="a family of quadratic curves with a cubic curve in purple", align=textClasses.TA_CENTERED)
        textbox.draw()
        canvas.flush()
        canvas.save()

    ToCanvas(canvas,frame)

    # now send it to a PIL canvas (this works on my machine but commented out because pil
    #                              may not be working on your machine-cwl )
    #import piddlePIL
    #canvas = piddlePIL.PILCanvas(size=(400,400), name='qtest.png')
    #ToCanvas(canvas,frame)
    
        
if __name__== '__main__':
    print('Running test drawing assorted quadratics to qtest.ps')
    import piddle
    runtest()

