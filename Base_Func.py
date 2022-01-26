# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 19:13:06 2021

@author: natha
"""
import math

WARNINGS = False

vowels = ('a','e','i','o','u')
NEAR_ZERO = 0.005
COLLISION_DIST = 2.5
DOCK_ANG_TOL = math.pi/4
PADDING = COLLISION_DIST*10
ANG_PADDING = math.pi/30
C_SIZE = 500
LETT_SIZE = C_SIZE/25
VOWEL_SIZE = LETT_SIZE/2
CUR_ND_TOL = 0.4
MINI_SIZE_RAT = 0.5
SMALL_SIZE_RAT = 0.85
LARGE_SIZE_RAT = 1.2
MINI_SEC_RAT = 3
SEC_RAT = 4
BIG_SEC_RAT = 5
OUTER_BIAS = math.pi/6
INNER_BIAS = math.pi/6
TYPE4_OUTER_SHRINK = 0.5
TYPE4_INNER_GROWTH = 0.5
TYPE4_OUTER_SHRINK_VOW = 0.65
TYPE4_INNER_GROWTH_VOW = 0.65
DOCK_SPACE = C_SIZE/50
DOCKMATCH_JIG_LIM = 15
CURVE_NOD_RAD_RAT_LIM = 3
DOUB_LETT_RAT = 0.9

numeric = ('-', '0','1','2','3','4','5','6','7','8','9')

def GalRad2MathDeg(radian):
    return radian/math.pi*180 - 90
def GalRad2MathRad(radian):
    return radian - math.pi/2
def MathRad2GalRad(radian):
    return (radian + math.pi/2) % (2*math.pi)

def Divot_Dist_func(Wrd_cir, lett_cir):
    divot_dist = Wrd_cir.outer_rad - lett_cir.inner_rad + 1
    circ_dist = Wrd_cir.inner_rad - lett_cir.outer_rad - 2*lett_cir.thickness
    semi_dist = Wrd_cir.outer_rad
    return (divot_dist, circ_dist, semi_dist)
def DotSize_func(Syllable):
    Radius= Syllable.radius
    if Syllable.secondary:
        Radius *= DOUB_LETT_RAT        
    if Syllable.docked:
        DotSize = min(Radius/6, VOWEL_SIZE)
        DotDist = Radius
    elif Syllable.text[-1] in ('e','i','u'):
        DotSize = Radius/3
        DotDist = Radius
    elif Radius > 0.4*Syllable.parent.radius:
        DotSize = Radius/5
        DotDist = 0.7*Radius
    else:
        DotSize = Radius/4
        DotDist = 0.5*Radius
    return DotSize, DotDist
def Semi_Spread_func(Syl):
    num = Syl.prime.cType[2]
    if num == 1:
        spread = (1,)
    elif num == 2:
        spread = (5/6, 7/6)
    elif num == 3:
        spread = (3/5, 1, 7/5)
    elif num == 4:
        spread = (1/2, 5/6, 7/6, 3/2)
    bound = Syl.prime.theta - 1.2*ANG_PADDING*(Syl.Loc.dist/Syl.parent.radius)**5
    spread = [(n - 1)*bound for n in spread]
    return tuple(map(lambda ang: ang + math.pi + Syl.Loc.ang, spread))
def Syl_Spread_func(lst, consons):
    num = len(lst)
    vowel_num = num - consons
    WEIGHT_FACTOR = 4
    n = math.pi/(consons + vowel_num/WEIGHT_FACTOR)
    ang = 0
    spread = []
    for i,syl in enumerate(lst):
        if lst[i-1] in vowels:
            ang += n/WEIGHT_FACTOR
        else:
            ang += n
        if i == 0:
            ang = 0
        spread.append(ang)
        if i + 1 == len(lst):
            if lst[0] in vowels:
                ang += n/WEIGHT_FACTOR
            else:
                ang += n
            continue
        if lst[i + 1] in vowels:
            ang += n/WEIGHT_FACTOR
        else:
            ang += n
    return spread
    
def Init_Dist_func(radius, num):
    print('TODO:implement doyle spiral')
    dist = 0.95*radius - Init_Rad_func(radius, num)
    dists = [dist]*num
    if num == 7 or num == 9:
        dists[-1] = 1
    return dists
def Init_Spread_func(num):
    spread = []
    if num == 7 or num == 9:
        spread.append(math.pi*2 - ANG_PADDING)
        num -= 1
    spread = [n*math.pi*2/num for n in range(num)] + spread
    return spread
def Init_Rad_func(radius, num):
    magic = {
        1:1,
        2:0.5,
        3:math.sqrt(3)/(math.sqrt(3)+2),
        4:1/(1+math.sqrt(2)),
        5:1/(1+math.sqrt(2*(1+1/math.sqrt(5)))),
        6:1/3,
        7:1/3,
        8:1/(1+math.sqrt(2*(2+math.sqrt(2)))),
        9:1/(1+math.sqrt(2*(2+math.sqrt(2))))
            }
    if num > 9:
        print('implent doyle spiral please')
        return radius/num
    if isinstance(num, float):
        a = math.floor(num)
        b = math.ceil(num)
        ans = (magic[a]*(b - num) + magic[b]*(num - a))
    else:
        ans = magic[num]
    return radius*ans

class Coord():
    Center = None
    Xord = 0
    Yord = 0
    Circle = None
    def __init__(self, Ord, Polar = True, Center = None, Frozen = False):           
        self.Set_Center(Center)
        self.lives = 1
        self.Frozen = Frozen
        if isinstance(Ord, Coord):
            self.Set_XY((Ord.Xord,Ord.Yord))
        elif Polar:
            self.Set_ang_d(Ord)
        else:
            self.Set_XY(Ord)
    
    def Ang2Coord(self, Ord, MathAng = False):
        Y1 = Ord.Yord - self.Yord
        X1 = Ord.Xord - self.Xord
        ang = math.atan2(Y1,X1)
        if MathAng:
            return ang
        else:
            return MathRad2GalRad(ang)
    
    def Destroy(self):
        self.Set_Center(None)
        self.Circle = None
    
    def Dist2Coord(self, Ord, XY = False, square = False):
        Y1 = Ord.Yord - self.Yord
        X1 = Ord.Xord - self.Xord
        if XY:
            return (X1, Y1)
        else:
            sq =  Y1**2 + X1**2
            if square:
                return sq
            else:
                return math.sqrt(sq)
            
    def Offsets(self):
        if self.NoCenter:
            Xoffset = 0
            Yoffset = 0
        else:
            Xoffset = self.Center.Xord
            Yoffset = self.Center.Yord
        return (Xoffset, Yoffset) 
    
    def ReScale(self, Scale, Frozen = None):
        if self in Frozen:
            return
        if self.Center is not None and self.Center not in Frozen:
            self.Center.ReScale(Scale, Frozen)
        (X,Y) = self.Offsets()
        self.Set_XY((X + math.sqrt(Scale)*self.dist*math.cos(GalRad2MathRad(self.ang)), 
                     Y + math.sqrt(Scale)*self.dist*math.sin(GalRad2MathRad(self.ang))))
        Frozen.add(self)
    
    def RotateA(self, target, angle, clockwise = False):
        restore = self.Center
        self.Set_Center(target)
        if clockwise:
            angle *= -1
        self.Shift_ang(angle)
        self.Set_Center(restore)    
    
    def Set_ang(self, ang):
        self.Set_ang_d((ang,self.dist))
    
    def Set_ang_d(self, ang_d):
        if self.Frozen:
            print(f'{self.Circle} is Frozen')
            raise RuntimeError
        self.ang = ang_d[0]
        self.dist = ang_d[1]
        self.ang_d = (self.ang, self.dist)
        self.Update_XY()
    
    def Set_Center(self, Center):
        if Center is self:
            raise RecursionError('You cannot set a Coord to be its own Center')
        if Center is not None:
            self.NoCenter = False
            if isinstance(Center, Coord):
                self.Center = Center
            elif isinstance(Center, (tuple, list)) and len(Center) == 2:
                if Center[0] == 0 and Center[1] == 0:
                    self.NoCenter = True
                    self.Center = None
                else:
                    self.Center = Coord((Center[0], Center[1]), False)
            else:
                raise TypeError('Center requires another Coord obj or a list/tuple of length 2')
        else:
            self.NoCenter = True
            self.Center = None
        self.Update_ang_d()
            
    
    def Set_dist(self, dist, *relative):
        if len(relative) > 0 and relative[0]:
            self.Set_ang_d((self.ang,self.dist*dist))
        else:
            self.Set_ang_d((self.ang,dist))
    
    def Set_X(self, X):
        self.Set_XY((X,self.Yord))
    
    def Set_XY(self, Ord, *relative):
        if self.Frozen:
            print(f'{self.Circle} is Frozen')
            raise RuntimeError
        if isinstance(Ord, Coord):
            Ord = (Ord.Xord, Ord.Yord)
        if len(relative) > 0 and relative[0]:
            self.Xord += Ord[0]
            self.Yord += Ord[1]
        else:
            self.Xord = Ord[0]
            self.Yord = Ord[1]
        self.XY = (self.Xord, self.Yord)
        self.Update_ang_d()
        
    def Set_Y(self, Y):
        self.Set_XY((self.Xord,Y))
    
    def Shift_ang(self, ang):
        if self.ang + ang > math.pi*2 or self.ang + ang < 0:
            if WARNINGS:
                print('Warning: attempt to shift past 2pi')
            return
        self.Set_ang(self.ang + ang)
        
    def Shift_dist(self, dist):
        if self.dist + dist <= 0:
            if WARNINGS:
                print('Warning: attempt to shift below 0 dist')
            return
        self.Set_dist(self.dist + dist)
    
    def Shift_CCW(self):
        self.Shift_ang(ANG_PADDING/2)    
    
    def Shift_CW(self):
        self.Shift_ang(-ANG_PADDING/2)
        
    def Update(self):
        self.Update_XY()
        self.Update_ang_d()
    
    def Update_XY(self):
        (Xoffset, Yoffset) = self.Offsets()
        self.Xord = Xoffset + self.dist*math.cos(GalRad2MathRad(self.ang))
        self.Yord = Yoffset + self.dist*math.sin(GalRad2MathRad(self.ang))
        self.XY = (self.Xord, self.Yord)
        
    def Update_ang_d(self):
        (Xoffset, Yoffset) = self.Offsets()
        Y1 = self.Yord - Yoffset
        X1 = self.Xord - Xoffset
        self.ang = (math.atan2(Y1, X1) + math.pi*5/2) % (2*math.pi) #Gal conversion is implicit
        self.dist = math.sqrt(Y1**2 + X1**2)
        if X1 == 0 and Y1 == 0 and WARNINGS:
            print('undefined angle sits on origin')
        self.ang_d = (self.ang, self.dist)
        
    def Vector(self, *length):
        Vec = (self.Xord - self.Center.Xord, 
               self.Yord - self.Center.Yord)
        if len(length) > 0 and length[0]:
            return (Vec, math.sqrt(Vec[0]**2 + Vec[1]**2))
        else:
            return Vec
    
    def __str__(self):
        return f'({self.Xord},{self.Yord})'
    
    def __repr__(self):
        return f' X:{self.Xord} Y:{self.Yord} Ang:{self.ang} dist:{self.dist}'
    
    def __add__(self, a):
        if isinstance(a, Coord):
            new_x = a.Xord + self.Xord
            new_y = a.Yord + self.Yord
        elif isinstance(a, (tuple, list)) and len(a) == 2:
            new_x = a[0] + self.Xord
            new_y = a[1] + self.Yord
        else:
            raise TypeError('__add__ requires another Coord obj or a length 2 list or tuple')
        if self.NoCenter:
            newCenter = None
        else:
            newCenter = self.Center
        new = Coord((new_x,new_y), False, Center = newCenter)
        new.Circle = self.Circle
        return new
    
    def __truediv__(self, a):
        if isinstance(a, (int, float)):
            new_x = self.Xord/a
            new_y = self.Yord/a
        elif isinstance(a, (tuple,list)) and len(a) == 2:
            new_x = self.Xord/a[0]
            new_y = self.Yord/a[1]
        else:
            raise TypeError('__truediv__ requires an int, or a length 2 list or tuple')
        if self.NoCenter:
            newCenter = None
        else:
            newCenter = self.Center
        new = Coord((new_x,new_y), False, Center = newCenter)
        new.Circle = self.Circle
        return new
    
    def __mul__(self, a):
        if isinstance(a, (float, int)):
            new_x = self.Xord*a
            new_y = self.Yord*a
        elif isinstance(a, (tuple,list)) and len(a) == 2:
            new_x = self.Xord*a[0]
            new_y = self.Yord*a[1]
        else:
            raise TypeError('__mul__ requires an int, or a length 2 list or tuple')
        if self.NoCenter:
            newCenter = None
        else:
            newCenter = self.Center
        new = Coord((new_x,new_y), False, Center = newCenter)
        new.Circle = self.Circle
        return new

    def __sub__(self, a):
        if isinstance(a, Coord):
            new_x = -a.Xord + self.Xord
            new_y = -a.Yord + self.Yord
        elif isinstance(a, (tuple, list)) and len(a) == 2:
            new_x = -a[0] + self.Xord
            new_y = -a[1] + self.Yord
        else:
            raise TypeError('__sub__ requires another Coord obj or a length 2 list or tuple')
        if self.NoCenter:
            newCenter = None
        else:
            newCenter = self.Center
        return Coord((new_x,new_y), False, Center = newCenter)
    
    def __eq__(self,a):
        if isinstance(a, Coord):
            if a.Xord == self.Xord and a.Yord == self.Yord:
                return True
        elif isinstance(a, (tuple, list)) and len(a) == 2:
            if a[0] == self.Xord and a[1] == self.Yord:
                return True
        else:
            raise TypeError('__eq__ requires another Coord obj or a length 2 list or tuple')
        return False
    
    def __hash__(self):
        return hash((self.Xord, self.Yord, self.Center))

def Syllablize(text, vow_splt = False, empty_dock = False, double_let = True, ext_alph = False, opt = None): 
    dock_letters = ('t','wh','sh','r','v','w','s')
    text = text.lower()
    syllables = []
    length = len(text)
    skip = False
    if opt is not None:
        if isinstance(opt, dict):
            vow_splt = opt['vow_splt']
            empty_dock = opt['empty_dock']
            double_let = opt['double_let']
            ext_alph = opt['ext_alph']
        else:
            vow_splt = opt[0]
            empty_dock = opt[1]
            double_let = opt[2]
            ext_alph = opt[3]
    for i in range(length):
        if skip:
            skip = False
            continue
        Syl = text[i]
        if text[i] in vowels:
            if not vow_splt:
                if i == 0:
                    pass
                elif double_let and text[i - 1] == Syl:
                    if len(syllables[-1]) > 2 and syllables[-1][-2] == Syl:
                        if len(syllables[-1]) > 3 and syllables[-1][-3:] == 'quu':
                            syllables[-1] = syllables[-1] + Syl
                        else:
                            syllables.append(Syl)
                    else:
                        syllables[-1] = syllables[-1] + Syl
                    continue
                elif text[i - 1] not in vowels or (i > 1 and text[i - 2:i] =='qu'):
                    if empty_dock and syllables[-1] in dock_letters:
                        syllables.append(Syl)
                    else:
                        syllables[-1] = syllables[-1] + Syl
                    continue
            elif Syl == 'u' and not ext_alph and i > 0 and text[i - 1] == 'q':
                syllables[-1] = 'qu'
        elif Syl == 'c':
            if ext_alph:
                if i + 1 < length and text[i + 1] == 'h':
                    skip = True
                    Syl ='ch'
            else:
                if  i == length - 1:
                    Syl = 'k'
                elif text[i + 1] == 'h':
                    skip = True
                    Syl ='ch'
                elif i == 0:
                    Syl = 'k'
                elif text[i + 1] in vowels:
                    if i + 2 < length and text[i+2] == 's':
                        Syl = 's'
                    elif text[i - 1] in vowels: 
                        Syl = 's'
                else:
                    Syl = 'k'
        elif Syl == 'h':
            if i == 0:
                pass
            elif text[i - 1] == 's':
                syllables[-1] = 'sh'
                continue
            elif text[i - 1] == 't':
                syllables[-1] = 'th'
                continue
            elif ext_alph:
                if text[i - 1] == 'p':
                    syllables[-1] = 'ph'
                    continue
                elif text[i - 1] == 'w':
                    syllables[-1] = 'wh'
                    continue
                elif text[i - 1] == 'g':
                    syllables[-1] = 'gh'
                    continue
        elif Syl == 'g' and i != 0 and text[i - 1] == 'n':
            syllables[-1] = 'ng'
            continue
        elif not ext_alph and Syl == 'q' and i < length - 1 and text[i + 1] != 'u':
            Syl = 'qu'
        if i == 0:
            syllables.append(Syl)
            continue
        if Syl == syllables[-1] and double_let:
            syllables[-1] = syllables[-1] + Syl
            continue
        syllables.append(Syl)
    return syllables
