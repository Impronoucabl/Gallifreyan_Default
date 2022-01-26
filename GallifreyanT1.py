# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 18:22:57 2021

@author: Impronoucabl
"""
import drawSvg as draw 

from Custom import Divot_Dist_func, DotSize_func, Semi_Spread_func
from Custom import Init_Dist_func, Init_Spread_func, Init_Rad_func
from Custom import Node_pair_Dash, Node_pair_Split_1
from Base_Func import *

def PreRender(size = None):
    if size is None:
        size = C_SIZE
    return draw.Drawing(size,size, origin = 'center')

class Circle():
    parent = None
    thickness = 0
    nxt = None
    prv = None
    def __init__(self,
                 Loc,
                 radius,
                 thickness,
                 Text,
                 settings = None,
                 parent = None):
        if isinstance(Loc, Coord):        
            self.Loc = Loc
        else:
            self.Loc = Coord(Loc)
        if self.Loc.Circle is None:
            self.Loc.Circle = self
        self.Set_radius(radius, True)
        self.Set_thick(thickness)
        self.text = Text
        self.Freeze = []
        self.Attachments = []
        self.children = []
        self.Rotation = 0
        self.spare_dash_nodes = set()
        self.Opt_dict = {
            'vow_splt':   False, 
            'empty_dock': False, 
            'double_let': False, 
            'ext_alph':   False,
            'lin_col':    'black',
            'b_col':      'white'
            }
        if settings is not None:
            if isinstance(settings, dict):
                for key, value in settings.items():
                    self.Opt_dict[key] = value
            else:
                raise RuntimeError('Settings is not a dict')
        if parent is not None:
            parent.children.append(self)
            self.parent = parent
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return f'{self.text} Rad {self.radius} Loc({self.Loc})'
    
    @staticmethod
    def _test(Cir1, Cir2, distance = False):
        dist = Cir1.Dist2Cir(Cir2)
        if distance:
            return dist
        else:
            if dist <= COLLISION_DIST:
                if WARNINGS:
                    print(f'Collision between {Cir1} & {Cir2}')
                return True
            return False
    
    def Backup(self, Loc_lst):
        LOC = self.Loc + (0,0)
        LOC.lives += self.Loc.lives
        unique = True
        for loc, cir_lst in Loc_lst:
            if loc.__hash__() == LOC.__hash__():
                cir_lst.append(self)
                unique = False
                break
        if unique:
            Loc_lst.append((LOC, [self]))
        for kids in self.children:
            kids.Backup(Loc_lst)
    
    def Center_Restore(self):
        if not self.Loc.NoCenter:
            self.Loc.Set_Center(self.Loc.Center.Circle.Loc)
        for kids in self.children:
            kids.Center_Restore()    
    
    def Collision_check(self, ignore_attach = True):
        Collision = False
        for Cir1 in self.children:
            if Cir1.text not in ('a','o'):
                if self._inner_loop(Cir1, self.children, ignore_attach = ignore_attach):
                    Collision = True
                    break
            if isinstance(Cir1, Syllable):
                if Cir1.prime.cType[0] == 4:
                    if self._inner_loop(Cir1, self.parent.children, ignore_attach = ignore_attach):                        
                        Collision =  True
                        break
                if Cir1.text[-1] in ('a','o'):
                    if self._inner_loop(Cir1.children[-1], self.children, ignore_attach = ignore_attach):
                        Collision = True
                        break
        return Collision
    
    def CspaceR(self, Lspace = None):
        if Lspace is None or not Lspace:
            target = self.nxt
        else:
            target = self.prv
        if target.text in ('a', 'o') and isinstance(target, Syllable):
            target = target.prime
        if self.text in ('a','o') and isinstance(self, Syllable):
            source = self.prime
        else:
            source = self
        return source.Dist2Cir(target)
    
    def Dist2Cir(self, Cir2):
        dist = self.Loc.Dist2Coord(Cir2.Loc)
        return dist - self.outer_rad - Cir2.outer_rad
    
    def _inner_loop(self, Cir1, group, ignore_attach = True):
        Collision = False
        Extras = []
        Life = []
        for Cir2 in group:
            if Cir1 is Cir2 or Cir2 is Cir1.parent:
                continue
            if isinstance(Cir1, Word) and ignore_attach:
                if Cir2 in [x.parent for x in Cir1.Attachments]:
                    continue
                if Cir1 in [x.parent for x in Cir2.Attachments]:
                    if len(Cir2.Attachments) > 1:
                        Extras += Cir2.Attachments
                    continue
                if Cir2 in [x.parent for x in Extras]:
                    continue
            if isinstance(Cir1, Syllable):
                if isinstance(Cir2, Word) and ignore_attach:
                    if any([True for Cir in Cir1.parent.children if Cir in Cir2.Attachments]):
                        continue
                    if any([True for Cir in Cir2.children if Cir in Cir1.parent.Attachments]):
                        continue                    
                if Cir2.text[-1] in ('a','o'):
                    Collision = self._test(Cir1, Cir2.children[-1])
                    if Collision:
                        break
            if isinstance(Cir1, (Consonant, Vowel)):
                if Cir2.parent is Cir1.parent:
                    continue
            if Cir2.text not in ('a','o'):
                Collision = self._test(Cir1,Cir2)
                if Collision:
                    if not ignore_attach:
                        break
                    Life.append(Cir2)
        deaths = len(Life)
        for Cir2 in Life:
            if Cir2 in [x.parent for x in Extras]:
                deaths -= 1
        if deaths == 0:
            return False
        else:
            return True
    
    def Node_gen(self):
        for kids in self.children:
            kids.Node_gen()
        if self.parent is not None:
            self.parent.spare_dash_nodes.update(self.spare_dash_nodes)
    
    def Node_pair(self, **options):
        if options['paired_nodes']:
            Node_pair_Dash(self)
        count = 0
        while len(self.spare_dash_nodes) > 0 and count < 100:
            Node_pair_Split_1(self)
            Node_pair_Split_1(self)
            count += 1
        if count > 99:
            print('Unfinished Node pairing')    
    
    def Render(self, canvas = None):
        for kids in self.children:
            kids.Render(canvas = canvas)
    
    def Restore(self, loc_lst):
        for point in loc_lst:
            if self in point[1]:
                self.Loc = point[0]
                break
        for kids in self.children:
            kids.Restore(loc_lst)
    
    def Rotate(self, angle):
        self.Rotation += angle
    
    def Set_radius(self, new_r, *relative):
        if len(relative) > 0 and relative[0]:
            self.radius = new_r
        else:
            self.radius *= new_r
        self.outer_rad = self.radius + self.thickness
        self.inner_rad = max(0,self.radius - self.thickness)
    
    def Set_thick(self, new_thick, *relative):
        if len(relative) > 0 and relative[0]:
            self.thickness *= new_thick
        else:
            self.thickness = new_thick
        self.outer_rad = self.radius + self.thickness
        self.inner_rad = max(0,self.radius - self.thickness)
    
    def Update(self):
        self.Loc.Update()
        for kids in self.children:
            kids.Update()

class Word(Circle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vow_anch = [False for n in ('e','i','o','u') if n in self.text]
        if len(vow_anch) == 0:
            self.Opt_dict['vow_splt'] = True
        self.docks = []
        self.txt_lst = Syllablize(self.text, opt=self.Opt_dict)
        self.consonants = 0
        for Syl in self.txt_lst:
            if Syl not in vowels:
                    self.consonants += 1
    
    def A_fix(self):
        for Syl in self.children:
            if 'a' in Syl.text:
                if any([wrd.Dist2Cir(Syl.children[-1]) < 0 for wrd in self.parent.children]):
                    Syl.children[-1].Loc.Set_ang(Syl.nxt.Loc.ang - Syl.nxt.prime.thi - ANG_PADDING)
                    Syl.Freeze.append(Syl.children[-1])
                    Syl.Update()
                    if WARNINGS:
                        print("A_fix activated!")
    
    def Attach_Space(self, Ignore = None):
        if Ignore is None:
            Ignore = []
        min_bound = []
        max_bound = []
        for dock in self.Attachments:
            if dock in Ignore:
                continue
            ang = dock.Loc.ang + math.pi
            max_bound.append(ang - dock.prime.theta2/2)
            min_bound.append(ang + dock.prime.theta2/2)
        if min_bound == [] or max_bound == []:
            return None
        min_bound = (max(min_bound) + 2*ANG_PADDING) % (2*math.pi)
        max_bound = (min(max_bound) - 2*ANG_PADDING) % (2*math.pi)
        return min_bound, max_bound
    
    def Condense(self):
        space = []
        for kids in self.children:
            space.append(kids.CspaceR())
        for n, kids in enumerate(self.children):
            if kids not in self.Freeze:
                if space[n] > space[n-1] and space[n] > ANG_PADDING:
                    if kids.Dist2Cir(kids.nxt.nxt) < COLLISION_DIST:
                        continue
                    kids.Loc.Shift_CCW()
                elif space[n] < space[n-1] and space[n-1] > ANG_PADDING:
                    if kids.Dist2Cir(kids.prv.prv) < COLLISION_DIST:
                        continue
                    kids.Loc.Shift_CW()
    
    def Grow(self):
        'space everything out first'
        count = 0
        if self.Collision_check():
            while self.Collision_check():
                count += 1
                if count > 20:
                    self.Shrink()
                    if count > 30:
                        print('No room for growth')
                        return
                else:
                    for kids in self.children:
                        if isinstance(kids.prime, Vowel):
                            min_size = VOWEL_SIZE
                        else:
                            min_size = LETT_SIZE
                        kids.Set_radius(max(kids.radius - 1, min_size), True)
                self.Condense()
                self.Update()
            for kids in self.children: 
                if kids not in self.Freeze:
                    (divot_dist, circ_dist, semi_dist) = Divot_Dist_func(self, kids)
                    if kids.prime.cType[0] == 1:
                        kids.Loc.Set_dist(divot_dist)
                    elif kids.prime.cType[0] == 2:
                        kids.Loc.Set_dist(circ_dist)
                    elif kids.prime.cType[0] == 3:
                        kids.Loc.Set_dist(semi_dist)
        count = 0 
        while not self.Collision_check():
            count += 1
            changes = 0
            for kids in self.children:
                if isinstance(kids.prime, Consonant):
                    if kids.radius >= 0.75*self.outer_rad or kids.docked:
                        continue
                    back_upDist = kids.Loc.dist
                    changes += 1
                    kids.Set_radius(min(kids.radius + 1, 0.75*self.outer_rad), True)
                    (divot_dist, circ_dist, semi_dist) = Divot_Dist_func(self, kids)
                    if kids.prime.cType[0] == 1:
                        kids.Loc.Set_dist(divot_dist)
                    elif kids.prime.cType[0] == 2:
                        kids.Loc.Set_dist(circ_dist)
                    elif kids.prime.cType[0] == 3:
                        kids.Loc.Set_dist(semi_dist)
                    elif kids.prime.cType[0] == 4:
                        self.Type4Push()
                    self.Jiggle()
                    for _ in range(1):
                        self.Condense()
                    if self.Collision_check():
                        kids.Set_radius(kids.radius - 1, True)
                        kids.Loc.Set_dist(back_upDist)
                        changes -= 1
            if changes == 0:
                print('No further changes')
                break
            if count > 125:
                print('Growth timed out')
                break
            if count == 13:
                A = 1
        self.A_fix()
    
    def Jiggle(self, space = None, Deep = None, Crash_stop = None):
        if space is None:
            space = self.Space_lst()
        if Crash_stop is None:
            Crash_stop = False
        if Deep is None:
            Deep = False
        if Crash_stop and self.Collision_check():
            return
        for n, kids in enumerate(self.children):
            if kids in self.Freeze:
                continue
            if len(space) > 3 and Deep:
                if n + 1 == len(space):
                    m = 0
                else:
                    m = n + 1
                if space[n-2] + space[n-1] < space[n] + space[m]:
                    if kids.Loc.ang < math.pi*2 - ANG_PADDING:
                        kids.Loc.Shift_CCW()
                elif space[n-2] +  space[n-1] > space[n] + space[m]:
                    if kids.Loc.ang > ANG_PADDING:
                        kids.Loc.Shift_CW()
            else:
                if space[n-1] < space[n]:
                    if kids.Loc.ang < math.pi*2 - ANG_PADDING:
                        kids.Loc.Shift_CCW()
                elif space[n-1] > space[n]:
                    if kids.Loc.ang > ANG_PADDING:
                        kids.Loc.Shift_CW()
        self.Update()
        return self.Space_lst()
    
    def Nearest_Dock(self, angle, cross_0 = None):
        if len(self.docks) == 0:
            return None
        if angle + DOCK_ANG_TOL/2 > math.pi*2 and cross_0 is not False:
            cross_0 = True
        lst = [abs(docks.Loc.ang - angle) for docks in self.docks]
        if cross_0 is True:
            lst = [abs((docks.Loc.ang - angle) % math.pi) for docks in self.docks]
        dock = min(lst)
        if dock < DOCK_ANG_TOL:
            return self.docks[lst.index(dock)]
        else:
            return None
    
    def Repel(self, ang, repeats = None, outer_only = None):
        if repeats is None:
            repeats = 1
        if outer_only is None:
            outer_only = False
        if isinstance(ang, Circle):
            ang = ang.Loc.ang 
        if len(self.children) == 1:
            diff = ang - self.children[0].Loc.ang
            if diff < -math.pi:
                diff += 2*math.pi
            elif diff > math.pi:
                diff -= 2*math.pi
            if diff < 0 and self.children[0].Loc.ang + 2*ANG_PADDING < math.pi*2:
                self.children[0].Loc.Shift_CCW()
            elif diff > 0 and self.children[0].Loc.ang > 2*ANG_PADDING:
                self.children[0].Loc.Shift_CW()  
            return
        for n in range(repeats):
            for kids in self.children:
                if kids in self.Freeze:
                    continue
                if outer_only and not (kids.prime.cType[0] == 4 or kids.text[-1] == 'a'):
                    continue
                diff = ang - kids.Loc.ang
                if diff < -math.pi:
                    diff += math.pi*2
                if diff < 0 and kids.Loc.ang + 2*ANG_PADDING < math.pi*2:
                    if kids.Rspace() > ANG_PADDING:
                        kids.Loc.Shift_CCW()
                elif diff > 0 and kids.Loc.ang > 2*ANG_PADDING:
                    if kids.Lspace() > ANG_PADDING:
                        kids.Loc.Shift_CW()                 
    
    def Shrink(self):
        self.Set_thick(0.95, True)
        for kids in self.children:
            if kids not in self.Freeze:
                if isinstance(kids.prime, Vowel):
                    num = -0.25
                else:
                    num = -1
                kids.Set_radius(kids.radius + num, True)
                kids.Set_thick(kids.thickness + num/2)
                (divot_dist, circ_dist, semi_dist) = Divot_Dist_func(self, kids)
                if kids.prime.cType[0] == 1:
                    kids.Loc.Set_dist(divot_dist)
                elif kids.prime.cType[0] == 2:
                    kids.Loc.Set_dist(circ_dist)
                elif kids.prime.cType[0] == 3:
                    kids.Loc.Set_dist(semi_dist)
    
    def Space_lst(self):
        return [x.Rspace() for x in self.children]
    
    def Syl_gen(self):
        sett = self.Opt_dict.copy()
        sett['vow_splt'] = True
        sett['double_let'] = False
        section_rad = Init_Spread_func(len(self.txt_lst))
        rad_size = LETT_SIZE
        'rad_size = Init_Rad_func(self.radius - PADDING, num)'
        for n,Syl in enumerate(self.txt_lst):
            Syll = Syllable(Coord((section_rad[n], self.radius), Center = self.Loc), 
                     rad_size,
                     self.thickness*0.5,
                     Syl,
                     settings = sett,
                     parent = self)
            if Syll.dock:
                self.docks.append(Syll)
            if n > 0:
                Syll.prv = self.children[-2]
                self.children[-2].nxt = Syll
        self.children[0].prv = self.children[-1]
        self.children[-1].nxt = self.children[0]
        
    def SkeleRend(self, canvas = None):
        arc_syl = []
        O_syl = []
        for Syl in self.children:
            Syl.Loc.Set_Center(self.Loc)
            Syl.Update()
            if Syl.prime.cType[0] in (1,3,4) or Syl.text in ('e','i','u'):
                arc_syl.append(Syl)
                if Syl.prime.cType[0] == 4 or Syl.text in ('e','i','u'):
                    O_syl.append(Syl)
        if len(arc_syl) == 0:
            canvas.append(draw.Circle(self.Loc.Xord,
                                      self.Loc.Yord,
                                      self.outer_rad,
                                      fill = self.Opt_dict['lin_col'],
                                      stroke = 'none'))
            canvas.append(draw.Circle(self.Loc.Xord,
                                      self.Loc.Yord,
                                      self.inner_rad,
                                      fill = self.Opt_dict['b_col'],
                                      stroke = 'none'))
        else:
            RingError = True
            for syl in arc_syl:
                if syl.prime.thi == 0:
                    print(f'Check {syl.prime.text} distance')
                    continue
                RingError = False
            if RingError:
                raise ValueError(f'Letters do not intersect {self.text} ring')
            outer_path = draw.Path(fill = self.Opt_dict['lin_col'], stroke = 'none')
            inner_path = draw.Path(fill = self.Opt_dict['b_col'],   stroke = 'none')
            Ostart = 0
            Istart = 0
            O_fin = math.pi*2
            I_fin = math.pi*2
            'Deal with first/last syllables overlapping at 0 degrees'
            skip_first = False
            skip_last = False
            if arc_syl[0] is self.children[0]:
                if arc_syl[0] in O_syl:
                    thiA = thiB = (arc_syl[0].prime.thi2 + arc_syl[0].prime.thi)/2
                else:
                    thiA = arc_syl[0].prime.thi2
                    thiB = arc_syl[0].prime.thi
                S_ang  = self.Rotation + arc_syl[0].Loc.ang - thiA
                S_ang2 = self.Rotation + arc_syl[0].Loc.ang - thiB
                if len(self.children) > 1 and S_ang > self.children[-1].Loc.ang:
                    S_ang -= math.pi*2
                    S_ang2 -= math.pi*2
                if S_ang < 0:
                    Ostart = S_ang
                    O_fin  = S_ang
                    skip_first = True
                if S_ang2 < 0:
                    Istart = self.Rotation + arc_syl[0].Loc.ang - thiB
                    I_fin  = Istart
                    skip_first = True
            if Ostart == 0 and I_fin == math.pi*2:
                if arc_syl[-1] is self.children[-1] and arc_syl[-1] is not self.children[0]:
                    if arc_syl[-1] in O_syl:
                        thiA = thiB = (arc_syl[-1].prime.thi2 + arc_syl[-1].prime.thi)/2
                    else:
                        thiA = arc_syl[-1].prime.thi2
                        thiB = arc_syl[-1].prime.thi
                    S_ang  = self.Rotation + arc_syl[-1].Loc.ang + thiA
                    S_ang2 = self.Rotation + arc_syl[-1].Loc.ang + thiB
                    if S_ang > math.pi*2:
                        Ostart = S_ang
                        O_fin  = S_ang
                        skip_last = True
                    if S_ang2 > math.pi*2:
                        Istart = self.Rotation + arc_syl[-1].Loc.ang + thiB
                        I_fin  = Istart
                        skip_last = True
            'Start drawing the ring'
            M = False
            L = False
            for Syl in arc_syl:
                if Syl in O_syl:
                    thi3 = (Syl.prime.thi2 + Syl.prime.thi)/2
                    arc_Ostrt = self.Rotation + Syl.Loc.ang - thi3
                    arc_Ofin  = self.Rotation + Syl.Loc.ang + thi3
                    arc_Istrt = self.Rotation + Syl.Loc.ang - thi3
                    arc_Ifin  = self.Rotation + Syl.Loc.ang + thi3
                else:
                    arc_Ostrt = self.Rotation + Syl.Loc.ang - Syl.prime.thi2
                    arc_Ofin  = self.Rotation + Syl.Loc.ang + Syl.prime.thi2
                    arc_Istrt = self.Rotation + Syl.Loc.ang - Syl.prime.thi
                    arc_Ifin  = self.Rotation + Syl.Loc.ang + Syl.prime.thi
                if Syl is self.children[0]:
                    M = True
                if skip_first:
                    skip_first = False
                else:
                    if Syl is arc_syl[0]:
                        outer_path.arc(self.Loc.Xord,
                                        self.Loc.Yord,
                                        self.outer_rad,
                                        GalRad2MathDeg(Ostart),
                                        GalRad2MathDeg(arc_Ostrt),
                                        cw = False,
                                        includeM = True)
                        inner_path.arc(self.Loc.Xord,
                                        self.Loc.Yord,
                                        self.inner_rad,
                                        GalRad2MathDeg(Istart),
                                        GalRad2MathDeg(arc_Istrt),
                                        cw = False,
                                        includeM = True)
                    else:
                        outer_path.arc(self.Loc.Xord,
                                        self.Loc.Yord,
                                        self.outer_rad,
                                        GalRad2MathDeg(Ostart),
                                        GalRad2MathDeg(arc_Ostrt),
                                        cw = False,
                                        includeM = M,
                                        includeL = L)
                        inner_path.arc(self.Loc.Xord,
                                        self.Loc.Yord,
                                        self.inner_rad,
                                        GalRad2MathDeg(Istart),
                                        GalRad2MathDeg(arc_Istrt),
                                        cw = False,
                                        includeM = M,
                                        includeL = L)
                    M = False
                if Syl in O_syl:
                    if Syl is not self.children[0]:
                        L = True
                    if isinstance(Syl.prime, Vowel):
                        out_rad = self.outer_rad - TYPE4_OUTER_SHRINK_VOW*self.thickness
                        inn_rad = self.inner_rad + TYPE4_INNER_GROWTH_VOW*self.thickness
                    else:
                        out_rad = self.outer_rad - TYPE4_OUTER_SHRINK*self.thickness
                        inn_rad = self.inner_rad + TYPE4_INNER_GROWTH*self.thickness
                    outer_path.arc(self.Loc.Xord,
                                        self.Loc.Yord,
                                        out_rad,
                                        GalRad2MathDeg(arc_Ostrt),
                                        GalRad2MathDeg(arc_Ofin),
                                        cw = False,
                                        includeM = M,
                                        includeL = L)
                    inner_path.arc(self.Loc.Xord,
                                        self.Loc.Yord,
                                        inn_rad,
                                        GalRad2MathDeg(arc_Istrt),
                                        GalRad2MathDeg(arc_Ifin),
                                        cw = False,
                                        includeM = M,
                                        includeL = L)
                    L = True
                else:
                    L = False
                    lett_Ostart = self.Rotation + (Syl.Loc.ang - Syl.prime.theta2 + math.pi*2) % (math.pi*2)
                    lett_Istart = self.Rotation + (Syl.Loc.ang - Syl.prime.theta + math.pi*2) % (math.pi*2)
                    lett_Ofin = self.Rotation + (Syl.Loc.ang + Syl.prime.theta2 + math.pi*2) % (math.pi*2)
                    lett_Ifin = self.Rotation + (Syl.Loc.ang + Syl.prime.theta + math.pi*2) % (math.pi*2)
                    outer_path.arc(Syl.Loc.Xord,
                                        Syl.Loc.Yord,
                                        Syl.prime.inner_rad,
                                        GalRad2MathDeg(lett_Ostart),
                                        GalRad2MathDeg(lett_Ofin),
                                        cw = True,
                                        includeM = M)
                    inner_path.arc(Syl.Loc.Xord,
                                        Syl.Loc.Yord,
                                        Syl.prime.outer_rad,
                                        GalRad2MathDeg(lett_Istart),
                                        GalRad2MathDeg(lett_Ifin),
                                        cw = True,
                                        includeM = M)
                Ostart = arc_Ofin
                Istart = arc_Ifin
            if not  skip_last:
                outer_path.arc(self.Loc.Xord,
                                    self.Loc.Yord,
                                    self.outer_rad,
                                    GalRad2MathDeg(Ostart),
                                    GalRad2MathDeg(O_fin),
                                    cw = False,
                                    includeM = False,
                                    includeL = L)
                inner_path.arc(self.Loc.Xord,
                                    self.Loc.Yord,
                                    self.inner_rad,
                                    GalRad2MathDeg(Istart),
                                    GalRad2MathDeg(I_fin),
                                    cw = False,
                                    includeM = False,
                                    includeL = L)
            outer_path.Z()
            inner_path.Z()
            canvas.append(outer_path)
            canvas.append(inner_path)

    def Type4Push(self):
        for Syl in self.children:
            dists = []
            if Syl.prime.cType[0] == 4:
                for Wrd in self.parent.children:
                    if Wrd is self:
                        continue
                    dists.append((Syl.Dist2Cir(Wrd), Wrd))
            if len(dists) == 0:
                continue
            closest = min(dists, key = lambda t: t[0])
            if closest[0] <= 2.5*COLLISION_DIST:
                angle = self.Loc.Ang2Coord(closest[1].Loc) - Syl.Loc.ang
                if angle > math.pi:
                    angle -= math.pi*2
                elif angle < -math.pi:
                    angle += math.pi*2
                if angle > 0 and Syl.Lspace() > 2*ANG_PADDING:
                    for n in range(2):
                        Syl.Loc.Shift_CW()
                elif angle < 0 and Syl.Rspace() > 2*ANG_PADDING:
                    for n in range(2):
                        Syl.Loc.Shift_CCW()        

class Sentence(Circle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)      
        self.txt_lst = self.text.split()
        self.dock_lst = []
        
    def Dock_Match(self, minnies, biggies):
        for wrd in self.children:
            for Syl in wrd.docks:
                if Syl.docked:
                    continue
                for wrd2 in self.children:
                    if wrd2 is wrd:
                        continue
                    angle = abs(Syl.Loc.Ang2Coord(wrd2.Loc) - Syl.Loc.ang)
                    if angle > math.pi:
                        angle -= 2*math.pi
                    tolerance = DOCK_ANG_TOL
                    if wrd in minnies or wrd2 in minnies:
                        tolerance *= 1.5
                    if wrd not in self.dock_lst:
                        tolerance *= 1.5
                    if abs(angle) < tolerance:
                        dist = Syl.Loc.Dist2Coord(wrd2.Loc)
                        ratio_lim = 1.5
                        if wrd in minnies or wrd2 in minnies:
                            ratio_lim *= 1/MINI_SIZE_RAT
                        if dist/wrd.radius <= ratio_lim:
                            print(f'docking {Syl} with {wrd2}')
                            if wrd2 in minnies:
                                move = True
                            else:
                                move = False
                            Dock_suc = self.Docking(Syl, wrd2, Wrd_Mv = move)
                            '''if Dock_suc:
                                Syl.parent.Freeze.remove(Syl)
                                for _ in range(DOCKMATCH_JIG_LIM):
                                    Syl.parent.Jiggle(Crash_stop = True)
                                wrd2.Loc.Set_XY(Syl.Loc)
                                Syl.parent.Freeze.append(Syl)'''
        self.Update()   
        
    def Docking(self, Syl, *Wrd, Update = None, Wrd_Mv = None, Retry = False):
        if Update is None:
            Update = False
        if Wrd_Mv is None:
            Wrd_Mv = False
        if Syl.parent.Loc.Frozen and not Wrd_Mv:
            print('Docking not possible')
            return False
        if Syl.docked and not Update:
            print('Dock already used')
            return False
        if any([True for x in Wrd[0].children if x in Syl.parent.Attachments]):
            print(f'{Wrd[0]} already docked with {Syl.parent}')
            return False
        if len(Wrd) == 1:
            if Syl.parent is Wrd[0]:
                return False
            if Wrd_Mv and self.children[0] in (Wrd[0], Syl.parent):
                print('bounce here?')
                if Retry:
                    return False
                return self.Docking(Syl, Wrd[0], Update = Update, Wrd_Mv = False, Retry = True)
            Revert = True
            Syl_Back = []
            Syl.parent.Backup(Syl_Back)
            Syl_Rad = Syl.radius
            Syl_par_rad = Syl.parent.radius
            Wrd_Back = []
            Wrd[0].Backup(Wrd_Back)
            backup = (Syl_Back, Syl_Rad, Syl_par_rad, Wrd_Back)
            
            'Move Syl into position'
            'Check if we need to rotate around the word'
            if len(Wrd[0].Attachments) > 1:
                (min_bound, max_bound) = Wrd[0].Attach_Space(Ignore = [Syl])
                ang = (Syl.parent.Loc.Ang2Coord(Wrd[0].Loc) + math.pi)%(2*math.pi)
                over = ang + Syl.prime.theta/2 - max_bound
                under = min_bound + Syl.prime.theta/2 - ang
                if min_bound > max_bound:
                    over -= math.pi*2
                    under -= math.pi*2
                if over > 0:
                    Syl.parent.Loc.RotateA(Wrd[0].Loc, over + ANG_PADDING, clockwise = True)
                    print(f'moving {Syl.parent} to avoid other docks')
                elif under > 0:
                    Syl.parent.Loc.RotateA(Wrd[0].Loc, under + ANG_PADDING, clockwise = False)
                    print(f'moving {Syl.parent} to avoid other docks')
                Syl.parent.Update()
            ang = Syl.parent.Loc.Ang2Coord(Wrd[0].Loc)
            remaining = ang - Syl.Loc.ang
            if not Syl.Loc.Frozen:                   
                count = 0
                while not Syl.parent.Collision_check():
                    if remaining > math.pi:
                        remaining -= 2*math.pi
                    if remaining > ANG_PADDING:
                        Syl.Loc.Shift_CCW()
                    elif remaining < - ANG_PADDING:
                        Syl.Loc.Shift_CW()
                    elif remaining == 0:
                        Revert = False
                        break
                    else:
                        Syl.Loc.Shift_ang(remaining)
                    if Syl.parent.Collision_check():
                        Syl.parent.Freeze.append(Syl)
                        Syl.parent.Repel(Syl)
                        Syl.parent.Jiggle()
                        Syl.parent.Freeze.pop()
                    if count > 100:
                        print('Movment timed out')
                        break
                    else:
                        count += 1
                        remaining = ang - Syl.Loc.ang
            if Revert:
                if remaining < DOCK_ANG_TOL and Wrd_Mv:
                    Revert = False
                else:
                    print('Docking not possible')
                    Syl.parent.Restore(Syl_Back)
                    Syl.parent.Center_Restore()
                    return False
            Syl.parent.Freeze.append(Syl)
            
            'Grow dock/space it out'
            rad = Wrd[0].outer_rad + Syl.thickness + Wrd[0].thickness + DOCK_SPACE
            remaining = rad - Syl.radius
            count = 0
            while remaining > COLLISION_DIST:
                if Syl.parent.Collision_check():
                    Syl.Loc.Shift_dist(1)
                    Syl.parent.Jiggle()
                else:
                    Syl.Set_radius(Syl.radius + COLLISION_DIST, True)
                Syl.Update()
                Syl.parent.Repel(Syl, repeats = 1)
                Syl.parent.Condense()
                remaining = rad - Syl.radius
                if Syl.prime.thi == 0:
                    Revert = True
                    break
                if count > 100:
                    print('Docking growth timed out')
                    Revert = True
                    break
                else:
                    count += 1
            Syl.Set_radius(rad, True)
            Syl.Update()
            if not Revert:
                while Syl.parent.Collision_check():
                    Syl.Loc.Shift_dist(1)
                    Syl.Update()
                    Syl.parent.Jiggle()
                    Syl.parent.Repel(Syl, 1)
                    Syl.parent.Condense()
                    if Syl.prime.thi == 0:
                        Revert = True
                        break
                    if count > 100:
                        print('Docking growth timed out')
                        Revert = True
                        break
                    else:
                        count += 1
            if Revert:
                print('Docking not possible')
                self.Revert(Syl, Wrd, backup)
                return False
            
            'move "a"s & type4s away from dock'
            if len(Wrd[0].Attachments) > 1:
                (min_bound, max_bound) = Wrd[0].Attach_Space()
                count = 0
                in_way = True
                while in_way and count < 100:
                    count += 1
                    in_way = False
                    angle = (min_bound + max_bound)/2
                    if len(Wrd[0].children) == 1:
                        if min_bound > max_bound:
                            angle += math.pi
                        Wrd[0].children[0].Loc.Set_ang(angle)
                    for W_Syl in Wrd[0].children:
                        if W_Syl.prime.cType[0] == 4 or W_Syl.text[-1] == 'a':
                            if min_bound > max_bound:
                                if W_Syl.Loc.ang < min_bound and W_Syl.Loc.ang > max_bound:
                                    in_way = True
                                    Wrd[0].Repel(angle, outer_only = True)
                            else:                                    
                                if W_Syl.Loc.ang > max_bound:
                                    in_way = True
                                    W_Syl.Loc.Shift_CW()
                                    Wrd[0].Jiggle(Crash_stop = True)
                                    W_Syl.Loc.Shift_CW()
                                elif W_Syl.Loc.ang < min_bound:
                                    in_way = True
                                    W_Syl.Loc.Shift_CCW()
                                    Wrd[0].Jiggle(Crash_stop = True)
                                    W_Syl.Loc.Shift_CCW()
                    if count >= 100:
                        print('Word_Syl movement timed out')
                    Wrd[0].Update()
            
            'move dock to word'
            count = 0
            if Wrd_Mv:
                Mover = Wrd[0]
                ang = Wrd[0].Loc.Ang2Coord(Syl.Loc)
            else:
                Mover = Syl.parent
                if Syl.parent.Loc.Dist2Coord(Wrd[0].Loc) < Syl.parent.radius:
                    ang = (ang + math.pi) % (2*math.pi)
            if WARNINGS:
                print(f'{Syl.parent},{Wrd[0]},{Mover},{Update}')
            Vector = (COLLISION_DIST*math.cos(GalRad2MathRad(ang)), 
                      COLLISION_DIST*math.sin(GalRad2MathRad(ang)))
            while Syl.Loc.Dist2Coord(Wrd[0].Loc) > COLLISION_DIST:
                Mover.Loc.Set_XY(Vector, True)
                Mover.Update()
                if count > 150:
                    print('Dock shift timed out')
                    Revert = True
                    break
                else:
                    count += 1
            if Wrd_Mv:
                Wrd[0].Loc.Set_XY(Syl.Loc)
            else:
                Syl.Loc.Set_XY(Wrd[0].Loc)
            if Revert:
                print('Docking not possible')
                self.Revert(Syl, Wrd, backup)
                return False
            else:
                Syl.parent.Update()
                compatible = True
                for other_docks in Mover.Attachments:
                    if other_docks is Syl:
                        continue
                    compatible = self.Docking(other_docks, Mover, Update = True, Wrd_Mv = False)
                    if not compatible:
                        print('Dock not compatible with exisiting docks')
                        self.Revert(Syl, Wrd, backup)
                        if Retry:
                            return False
                        else:
                            return self.Docking(other_docks, Mover, Update = Update, Wrd_Mv = True, Retry = True)
                if not Update:
                    Wrd[0].Attachments.append(Syl)
                    Syl.docked = True
                    print('Docking successful')
                    if Syl.parent not in self.dock_lst:
                        self.dock_lst.append(Syl.parent)
            Wrd[0].Update()   
        return True
    
    def Generate(self, iterations = 1, preview = None, nodes = None, **Options):
        default = {
            'grow': True,
            'paired_nodes': True
            }
        for (key, value) in Options.items():
            default[key] = value
        if preview is None:
            preview = False
        if nodes is None:
            nodes = True
        if not preview:
            (minnies, biggies) = self.Skele_Size()
            (minnies, biggies) = self.Skele_Dock(minnies = minnies, biggies = biggies)
            grow = False
            for n in range(iterations):
                self.Dock_Match(minnies, biggies)
                if n == iterations - 1:
                    grow = default['grow']
                self.Skele_Pol(minnies, biggies, Grow = grow)
        canvas = self.SkeleRend()
        if nodes:
            self.Nodes(**default)
            self.Render(canvas)
        print(self.text)
        return canvas
    
    def Jiggle(self):
        dist = [wrd.Dist2Cir(wrd.nxt) for wrd in self.children]
        for n, wrd in enumerate(self.children):
            if dist[n] > dist[n-1]:
               wrd.Loc.Shift_CCW()
            elif dist[n] < dist[n-1]:
               wrd.Loc.Shift_CW()
    
    def Nodes(self, **Options):
        self.Node_gen()
        self.Node_pair(**Options)
    
    def Pull_in(self):
        dists = [kid.Loc.dist - kid.outer_rad for kid in self.children]
        for _ in range(len(dists)):
            furthest = self.children[dists.index(max(dists))]
            if furthest not in self.dock_lst and furthest.Attachments == []:
                furthest.Loc.Shift_dist(-COLLISION_DIST)
                break
            else:
                dists.remove(max(dists))
        if self.Collision_check():
            furthest.Loc.Shift_dist(COLLISION_DIST)
            return False
        return True
    
    def Seperate(self):
        lst = self.children.copy()
        movements = [[]]*len(lst)
        for n, wrd in enumerate(self.children):
            lst.remove(wrd)
            for m, wrd2 in enumerate(lst):
                if wrd.Dist2Cir(wrd2) <= COLLISION_DIST:
                    movements[n].append(wrd2)
                    movements[n + m + 1].append(wrd)
        shift_dir = []
        for n, wrd_lst in enumerate(movements):
            sum_x = 0
            sum_y = 0
            for wrd in wrd_lst:
                ang = self.children[n].Loc.Ang2Coord(wrd.Loc, MathAng = True)
                sum_x += COLLISION_DIST*math.cos(ang + math.pi)
                sum_y += COLLISION_DIST*math.sin(ang + math.pi)
            shift_dir.append((sum_x,sum_y))
        for n, wrd in enumerate(self.children):
            wrd.Loc.Set_XY(shift_dir[n], True)
            wrd.Update()
        return
    
    def Skele_Size(self):
        if len(self.children) == 0:
            self.Word_Gen()
        minnies = []
        biggies = []
        big_mini = False
        for wrd in self.children:
            if wrd.consonants <= 1:
                for x in ('j','k','l','m','n','c'):
                    if x in wrd.text and 'o' in wrd.text:
                        big_mini = True
                        if x + 'o' in wrd.text:
                            big_mini = False
                        break
                if big_mini:
                    big_mini = False
                    wrd.Set_radius((SMALL_SIZE_RAT + MINI_SIZE_RAT)/2/MINI_SIZE_RAT)
                    wrd.Set_thick((SMALL_SIZE_RAT + MINI_SIZE_RAT)/2/MINI_SIZE_RAT, True)
                if wrd.prv.consonants > 5:
                    wrd.Set_radius(1/0.95)
                wrd.Set_radius(MINI_SIZE_RAT)
                wrd.Set_thick(MINI_SIZE_RAT, True)
                minnies.append(wrd)
            elif wrd.consonants <= 2:
                if wrd.prv.consonants > 5:
                    wrd.Set_radius(1/0.95)
                wrd.Set_radius(SMALL_SIZE_RAT)
                wrd.Set_thick(SMALL_SIZE_RAT, True)
            elif wrd.consonants >= 5:
                if wrd.prv.radius == wrd.radius:
                    wrd.prv.Set_radius(0.95)
                if wrd.nxt.radius == wrd.radius:
                    wrd.nxt.Set_radius(0.95)
                wrd.Set_radius(LARGE_SIZE_RAT)
                biggies.append(wrd)
            wrd.Update()
        if len(minnies) > 1:
            sections = 0
            for wrd in self.children:
                if wrd in minnies or wrd.nxt in minnies:
                    sections += MINI_SEC_RAT
                elif wrd in biggies or wrd.nxt in biggies:
                    sections += BIG_SEC_RAT
                else:
                    sections += SEC_RAT
            section_rad = 2*math.pi/sections
            angle = 0
            for wrd in self.children:
                wrd.Loc.Set_ang(angle)
                if wrd in minnies:
                    angle += MINI_SEC_RAT*section_rad/2
                elif wrd in biggies:
                    angle += BIG_SEC_RAT*section_rad/2
                else:
                    angle += SEC_RAT*section_rad/2
                if wrd.nxt in minnies:
                    angle += MINI_SEC_RAT*section_rad/2
                elif wrd.nxt in biggies:
                    angle += BIG_SEC_RAT*section_rad/2
                else:
                    angle += SEC_RAT*section_rad/2
            self.Update()
        if len(self.children) > 8:
            self.children[-1].Loc.Set_dist(0.25, True)
            if self.children[-1] in minnies:
                wrd.Set_radius(1/MINI_SIZE_RAT)
                wrd.Set_thick(1/MINI_SIZE_RAT, True)
                minnies.remove(self.children[-1])
            wrd.Set_radius(LARGE_SIZE_RAT)
            for n, kids in enumerate(reversed(self.children)):
                if n == 0:
                    new_angle = (kids.Loc.ang + math.pi*4)/3
                else:
                    new_angle = (n*kids.Loc.ang + 4*self.children[-1].Loc.ang)/(n + 2)
                kids.Loc.Shift_ang(((len(self.children) - n)/len(self.children))*(new_angle - kids.Loc.ang))
            self.Update()
        count = 0
        while self.Collision_check():
            self.Seperate()
            if count > 100:
                raise RuntimeError('Init Skele Collision')
            else:
                count += 1
        for _ in range(5):
            self.Jiggle()
        return minnies, biggies
    
    def Skele_Dock(self, minnies = None, biggies = None):
        if minnies is None:
            if biggies is None:
                (minnies, biggies) = self.Skele_Size()
            else:
                raise RuntimeError('minnies is specified, but biggies is not')
        for wrd in self.children:
            wrd.Syl_gen()
            wrd.Type4Push()
        if len(self.children) <= 1:
            return minnies, biggies
        'procedural docking'
        for wrd in self.children:
            if len(wrd.docks) == 0:
                continue
            bias = math.pi/2
            rel_dist = wrd.Loc.dist/self.radius
            if  rel_dist >= 0.75:
                bias += OUTER_BIAS
            elif rel_dist <= 0.4:
                bias -= INNER_BIAS
            ang = wrd.Loc.ang + bias
            dock = wrd.Nearest_Dock(ang)
            docked = False
            if dock is not None:
                if wrd.nxt is self.children[0]:
                    continue
                print(f'docking {dock} with {wrd.nxt}')
                docked = self.Docking(dock,wrd.nxt)
                if not docked and wrd.nxt is not self.children[0]:
                    docked = self.Docking(dock, wrd.nxt, Wrd_Mv = True)
            if not docked:
                ang = wrd.Loc.ang - bias
                dock = wrd.Nearest_Dock(ang)
                if dock is not None:
                    print(f'docking {dock} with {wrd.prv}')
                    docked = self.Docking(dock, wrd.prv)     
                    if not docked:
                        docked = self.Docking(dock, wrd.prv, Wrd_Mv = True)
        return minnies, biggies
                
    def Skele_Pol(self, minnies, biggies, Grow = None):
        if Grow is None:
            Grow = True
        if len(self.children) > 1:
            count = 0
            while not self.Collision_check():    
                Pulled = self.Pull_in()
                Centered = self.ReCenter(stepsize = 0.2)
                if count > 100:
                    print('Polish timed out')
                    break
                elif not Centered and not Pulled:
                    print('Center/Pull limit reached')
                    break
                else:
                    count += 1
        if Grow:
            for wrd in self.children:
                if wrd in minnies:
                    wrd.Update()
                    continue
                wrd.Grow()
    
    def ReCenter(self, stepsize = None):
        if stepsize is None:
            stepsize = 1
        Xmid = 0
        Ymid = 0
        for kids in self.children:
            Xmid += kids.Loc.Xord 
            Ymid += kids.Loc.Yord
        if abs(Xmid) <= NEAR_ZERO and abs(Ymid) <= NEAR_ZERO:
            return False
        for kids in self.children:
            kids.Loc.Set_XY((-Xmid*stepsize,-Ymid*stepsize), True)
            kids.Update()
        return True
    
    def Revert(self, Syl, Wrd, backup):
        (Syl_Back, Syl_Rad, Syl_par_rad, Wrd_Back) = backup
        Syl.Set_radius(Syl_Rad, True)
        Syl.parent.Set_radius(Syl_par_rad, True)
        Syl.parent.Restore(Syl_Back)
        Wrd[0].Restore(Wrd_Back)
        Syl.parent.Center_Restore()
        Wrd[0].Center_Restore()
        Syl.parent.Freeze.remove(Syl)
        print('Centers restored!')
    
    def SkeleRend(self, canvas = None):
        if canvas is None:
            canvas = PreRender(C_SIZE)
            canvas.append(draw.Rectangle(-C_SIZE/2,-C_SIZE/2,C_SIZE,C_SIZE, fill=self.Opt_dict['b_col']))
        canvas.append(draw.Circle(self.Loc.Xord,
                                  self.Loc.Yord,
                                  self.outer_rad,
                                  fill = self.Opt_dict['lin_col'],
                                  stroke = 'none'))
        canvas.append(draw.Circle(self.Loc.Xord,
                                  self.Loc.Yord,
                                  self.inner_rad,
                                  fill = self.Opt_dict['b_col'],
                                  stroke = 'none'))
        for wrd in self.children:
            wrd.SkeleRend(canvas = canvas)
        return canvas
    
    def Update(self):
        super().Update()
        Dock_Suc = True
        for kids in self.children:
            for docks in kids.Attachments:
                if docks in docks.parent.Freeze:
                    docks.parent.Freeze.remove(docks)
                Dock_Suc = self.Docking(docks, kids, Update = True, Wrd_Mv = True)
        return Dock_Suc
    
    def Word_Gen(self):
        num = len(self.txt_lst)
        if num == 0:
            return
        section_rad = Init_Spread_func(num)
        rad_size = Init_Rad_func(self.radius  - 2*PADDING,num)
        distance = Init_Dist_func(self.radius,num)
        sett = self.Opt_dict.copy()
        for n, wrd in enumerate(self.txt_lst):
            blah = Word(Coord((section_rad[n], distance), Center = (0,0)), 
                 rad_size, 
                 self.thickness*0.7, 
                 wrd.lower(),
                 settings = sett,
                 parent = self)
            if n > 0:
                blah.prv = self.children[-2]
                self.children[-2].nxt = blah
        self.children[0].prv = self.children[-1]
        self.children[-1].nxt = self.children[0]
    
class Syllable(Circle):
    dock = False
    docked = False
    prime = None
    secondary = False
    children = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.txt_lst = Syllablize(self.text, opt=self.Opt_dict)
        Vsett = self.Opt_dict.copy()
        Csett = self.Opt_dict.copy()
        for n, let in enumerate(self.txt_lst):
            if let in vowels:
                Lett = Vowel( self.Loc, 
                              self.radius,
                              self.thickness,
                              let,
                              settings = Vsett,
                              parent = self)
            else:
                Lett = Consonant( self.Loc, 
                                  self.radius,
                                  self.thickness,
                                  let,
                                  settings = Csett,
                                  parent = self)
            if n == 0:
                self.prime = Lett
                if Lett.text in ('t','wh','sh','r','v','w','s'):
                    self.dock = True
                (divot_dist, circ_dist, semi_dist) = Divot_Dist_func(self.parent, self)
                if Lett.cType[0] == 0:
                    self.Set_radius(VOWEL_SIZE, True)
                elif Lett.cType[0] == 1:
                    self.Loc.Set_dist(divot_dist)
                elif Lett.cType[0] == 2:
                    self.Loc.Set_dist(circ_dist)
                elif Lett.cType[0] == 3:
                    self.Loc.Set_dist(semi_dist)
                else:
                    continue
                self.Update()
            else:
                if self.prime.text == Lett.text:
                    self.secondary = True
                    self.Set_radius(1.1)
                    Lett.Set_radius(DOUB_LETT_RAT)
                    Lett.Set_thick(0.5, True)
                    self.prime.Set_thick(0.5, True)
                if Lett.cType[0] == 0:
                    Lett.Set_radius(VOWEL_SIZE, True)
    
    def Lspace(self):
        return self.Rspace(Lspace = True)
    
    def Node_gen(self):
        for kids in self.children:
            if self.secondary and kids is self.prime:
                continue
            kids.Node_gen()
        if self.parent is not None:
            self.parent.spare_dash_nodes.update(self.spare_dash_nodes)
    
    def Rspace(self, Lspace = None):
        revert = False
        if self.nxt.Loc.Center is not self.Loc.Center or self.prv.Loc.Center is not self.Loc.Center:
            revert = True
            back_upNxt = self.nxt.Loc.Center
            back_up = self.Loc.Center
            back_upPrv = self.prv.Loc.Center
            self.nxt.Loc.Set_Center(self.nxt.parent.Loc)
            self.Loc.Set_Center(self.parent.Loc)
            self.prv.Loc.Set_Center(self.prv.parent.Loc)
        if Lspace is not None and not Lspace:
            A = self.Loc.ang - self.prime.thi
            B = self.prv.Loc.ang + self.prv.prime.thi
        else:
            A = self.nxt.Loc.ang - self.nxt.prime.thi
            B = self.Loc.ang + self.prime.thi
        space = A - B
        if Lspace is None and self.nxt.Loc.ang < self.Loc.ang:
            space += math.pi*2
        if Lspace and space < 0:
            space += math.pi*2
        if revert:
            self.nxt.Loc.Set_Center(back_upNxt)
            self.Loc.Set_Center(back_up)
            self.prv.Loc.Set_Center(back_upPrv)
        return space
    
    def Set_radius(self, new_r, *relative):
        super().Set_radius(new_r, *relative)
        for cir in self.children:
            if isinstance(cir, Consonant):
                cir.Set_radius(new_r, *relative)
                if cir is not self.prime:
                    cir.Set_radius(DOUB_LETT_RAT)                    
            elif cir is self.prime:
                cir.Set_radius(new_r, *relative)
            
    def Set_Loc(self, Loc):
        for kids in self.children:
            if kids.text in ('a','o'):
                kids.Set_Center(Loc)
            else:
                kids.Loc = Loc
        
    def Update(self):
        for kids in self.children:
            if kids.text == 'o':
                if self.prime.cType[2] > 0:
                    for nodes in self.prime.children:
                        if abs(nodes.Loc.ang - kids.Loc.ang) - kids.thi2 < ANG_PADDING:
                            kids.Loc.Shift_ang(137.51/180*math.pi)
            elif kids not in self.Freeze:
                kids.Loc.Set_ang(self.Loc.ang)
        super().Update()

class Letter(Circle):
    cDict = {# (cType, feature Type, feature number)
        'b' : (1,0,0), #No features
        'j' : (2,0,0),
        't' : (3,0,0),
        'th': (4,0,0),
        'ch': (1,1,2), #Dots
        'k' : (2,1,2),
        'sh': (3,1,2),
        'y' : (4,1,2),
        'd' : (1,1,3),
        'l' : (2,1,3),
        'r' : (3,1,3),
        'z' : (4,1,3),
        'g' : (1,2,1), #Dashes
        'n' : (2,2,1),
        'v' : (3,2,1),
        'qu': (4,2,1),
        'h' : (1,2,2),
        'p' : (2,2,2),
        'w' : (3,2,2),
        'x' : (4,2,2),
        'f' : (1,2,3),
        'm' : (2,2,3),
        's' : (3,2,3),
        'ng': (4,2,3),
        'a' : (0,0,0), #vowels
        'e' : (0,0,0),
        'i' : (0,2,1),
        'o' : (0,0,0),
        'u' : (0,2,1),
        'ph': (2,1,1), #Extended alphabet
        'wh': (3,1,1),
        'gh': (4,1,1),
        'c' : (2,1,4),
        'q' : (4,1,4)
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cType = self.cDict.get(self.text)
        self.Theta(self.parent.parent)
        self.Thi(self.parent.parent)
        
    def Node_gen(self):
        if self.cType[2] > 0:
            if self.cType[1] == 1:
                Type = 'Dot'
            elif self.cType[1] == 2:
                Type = 'Dash'
            sett = self.Opt_dict.copy()
            num = self.cType[2]
            section_rad = Init_Spread_func(num)
            if self.cType[0] == 3:
                section_rad = Semi_Spread_func(self.parent)
            for n in range(self.cType[2]):
                N = Node(Coord(((section_rad[n] + self.Loc.ang)%(2*math.pi), self.radius), Center = self.Loc),
                                0,
                                2,
                                Type,
                                settings = sett,
                                parent = self)
                N.Update()
            super().Node_gen()
    
    def Render(self, canvas = None):
        if self.text.lower() in ('a', 'o') and self is self.parent.prime:
            self.parent.Loc.Shift_ang(self.parent.parent.Rotation)
        else:
            self.Loc.Shift_ang(self.parent.parent.Rotation)
        self.Update()
        canvas.append(draw.Circle(self.Loc.Xord,
                                  self.Loc.Yord,
                                  self.radius,
                                  fill = 'none',
                                  stroke = self.Opt_dict['lin_col'],
                                  stroke_width = 2*self.thickness))           
        super().Render(canvas = canvas)
    
    def Theta(self, Wrd):
        dist = self.parent.Loc.dist
        try:
            self.theta  = math.acos((Wrd.inner_rad**2 - dist**2 - self.outer_rad**2)/(2*dist*self.outer_rad))
            self.theta2 = math.acos((Wrd.outer_rad**2 - dist**2 - self.inner_rad**2)/(2*dist*self.inner_rad))
        except ValueError:
            self.theta  = 0
            self.theta2 = 0
        return self.theta
    
    def Thi(self, Wrd):
        dist = self.parent.Loc.dist
        try:
            self.thi  = math.acos((Wrd.inner_rad**2 + dist**2 - self.outer_rad**2)/(2*dist*Wrd.inner_rad))
            self.thi2 = math.acos((Wrd.outer_rad**2 + dist**2 - self.inner_rad**2)/(2*dist*Wrd.outer_rad))
        except ValueError:
            self.thi  = 0
            self.thi2 = 0
        return self.thi
    
    def Update(self):
        self.Theta(self.parent.parent)
        self.Thi(self.parent.parent)
        super().Update()

class Consonant(Letter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def Render(self,canvas):
        if self.cType[0] not in (1,3):
            super().Render(canvas = canvas)
        else:
            for kids in self.children:
                kids.Render(canvas = canvas)

class Vowel(Letter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Set_thick(0.9,True)
        self.True_ang = math.pi
        if self.text == 'a':
            self.True_ang = 0
            distance = self.parent.parent.outer_rad + self.outer_rad/2 + self.thickness
            self.Loc = Coord((self.Loc.ang + self.True_ang, distance), True, self.parent.parent.Loc)
        elif self.text == 'o':
            self.Loc = Coord((self.Loc.ang + self.True_ang, self.parent.radius), True, self.Loc)
        else:
            return
        self.Loc.Circle = self
    
    def Node_gen(self):
        super().Node_gen()
        if self.text == 'i':
            self.children[0].Loc.Shift_ang(math.pi)
        if self.parent.prime.cType[0] == 4 and self.text == 'a':
            self.Loc.Set_dist(self.Loc.dist + self.parent.radius) 
    
    def Update(self):
        if self.text == 'o':
            if self.parent.prime is self:
                self.Loc.Set_ang_d(((self.parent.Loc.ang + self.True_ang) % (2*math.pi),
                                   self.parent.thickness + self.outer_rad + 2*self.thickness))
            else:
                self.Loc.Set_dist(self.parent.radius)
        elif self.text == 'a':
            if self not in self.parent.Freeze:
                self.Loc.Set_ang((self.parent.Loc.ang + self.True_ang)%(2*math.pi))
        super().Update()
        
class Node(Circle):
    nType = None
    Drawn = False
    pair = None
    min_ang = 0
    max_ang = math.pi*2
    
    def angle_check(self, angle):
        self.parent.Update()
        s_test = False
        angle = (angle + 2*math.pi) % (2*math.pi)
        for lett in self.parent.parent.children:
            for sibling in lett.children:
                if sibling is self:
                    continue
                sib_ang = None
                if sibling.text == 'Dash' and sibling.pair is not None:
                    if sibling.pair.text =='Dash':
                        sib_ang = self.parent.Loc.Ang2Coord(sibling.pair.parent.Loc)
                    elif sibling.pair.text == 'Center':
                        sib_ang = sibling.Loc.ang
                elif sibling.text == 'Dot':
                    sib_ang = sibling.Loc.ang
                if sib_ang is None:
                    continue
                if abs(sib_ang - angle) < ANG_PADDING:
                    return False
        if self.min_ang % (math.pi*2) == self.max_ang % (math.pi*2):
            s_test = True
        else:
            if self.min_ang < self.max_ang:
                if self.min_ang + 2*ANG_PADDING < angle < self.max_ang - 2*ANG_PADDING:
                    s_test = True
            elif angle > min(math.pi*2, self.min_ang + 2*ANG_PADDING) or angle < max(0,self.max_ang - 2*ANG_PADDING):
                s_test = True
        return s_test
    
    def Node_check(self, node):
        angle = self.parent.Loc.Ang2Coord(node.parent.Loc)
        s_test = self.angle_check(angle)
        n_test = node.angle_check(angle + math.pi)
        if s_test and n_test:
            return True
        else:
            return False
    
    def Node_gen(self):
        if self.text is None:
            return
        elif self.text == 'Dot':
            (DotSize, DotDist) = DotSize_func(self.parent.parent)
            self.Set_thick(DotSize)
            self.Loc.Set_dist(DotDist)
        elif self.text == 'Dash':
            if self.pair is None:
                self.parent.spare_dash_nodes.add(self)            
        elif self.text == 'Center':
            pass
        
    def pair_node(self, node, angle = None):
        if angle is None:
            angle = self.parent.Loc.Ang2Coord(node.parent.Loc)
        self.pair = node
        node.pair = self
        self.Loc.Set_ang(angle)
        node.Loc.Set_ang((math.pi + angle) % (2*math.pi))
        
    def Render(self, canvas = None):
        if self.Drawn:
            return
        if self.text == 'Dot':
            canvas.append(draw.Circle(self.Loc.Xord,
                                    self.Loc.Yord,
                                    self.outer_rad,
                                    fill = self.Opt_dict['lin_col'],
                                    stroke = 'none'))
        elif self.text == 'Dash':
            if self.pair is None:
                (vector, vec_leng)= self.Loc.Vector(True)
                sent = self.parent.parent.parent.parent
                n = sent.radius/vec_leng
                residual = (self.Loc.Xord + n*vector[0])**2 + (self.Loc.Yord + n*vector[1])**2 - sent.radius**2
                count = 0
                lower = 0
                upper = n*2
                while  abs(residual) > sent.thickness:
                    count += 1
                    if residual > 0:
                        upper = min(n, upper)
                    else:
                        lower = max(n, lower)
                    n = (upper + lower)/2
                    residual = (self.Loc.Xord + n*vector[0])**2 + (self.Loc.Yord + n*vector[1])**2 - sent.radius**2
                    if count > 50:
                        print(f"{self.parent.text} wall-dash Timed out")
                        break
                canvas.append(draw.Line(self.Loc.Xord,
                                    self.Loc.Yord,
                                    self.Loc.Xord + n*vector[0],
                                    self.Loc.Yord + n*vector[1],
                                    stroke = self.Opt_dict['lin_col'],
                                    stroke_width = self.thickness))
            elif self.pair.text == 'Dash':
                canvas.append(draw.Line(self.Loc.Xord,
                                    self.Loc.Yord,
                                    self.pair.Loc.Xord,
                                    self.pair.Loc.Yord,
                                    stroke = self.Opt_dict['lin_col'],
                                    stroke_width = self.thickness))
                self.pair.Drawn = True
            elif self.pair.text == 'Center':
                self.pair.Render(canvas = canvas)            
            ''' Debug rendering
            canvas.append(draw.Circle(self.pair[0].Loc.Xord,
                                    self.pair[0].Loc.Yord,
                                    5,
                                    fill = 'red',
                                    stroke = 'none'))
            canvas.append(draw.Circle(self.pair[1].Loc.Xord,
                                    self.pair[1].Loc.Yord,
                                    5,
                                    fill = 'red',
                                    stroke = 'none'))
            canvas.append(draw.Circle(self.Loc.Xord,
                                    self.Loc.Yord,
                                    5,
                                    fill = 'blue',
                                    stroke = 'none'))
            '''
        self.Drawn = True
        
    def Update(self):  
        self.Drawn = False
        self.Loc.Set_Center(self.parent.Loc)
        if self.text == "Dot":
            (DotSize, DotDist) = DotSize_func(self.parent.parent)
            self.Set_thick(DotSize)
            self.Loc.Set_dist(DotDist)
            if self.parent.cType == 3:
                self.min_ang = self.parent.Loc.ang + self.parent.theta2 + ANG_PADDING
                self.max_ang = self.parent.Loc.ang - self.parent.theta2 - ANG_PADDING
        elif self.text == "Dash":
            self.Loc.Set_dist(self.parent.radius)
            if self.parent.cType[0] in (1,3):
                if self.parent.cType[0] == 1:
                    theta = self.parent.theta
                else:
                    theta = self.parent.theta2
                self.min_ang = self.parent.Loc.ang + theta + ANG_PADDING
                self.max_ang = self.parent.Loc.ang - theta - ANG_PADDING
            elif self.parent.text == 'i':
                self.min_ang = self.parent.Loc.ang + math.pi/2 + ANG_PADDING
                self.max_ang = self.parent.Loc.ang - math.pi/2 - ANG_PADDING
            elif self.parent.text == 'u':
                self.min_ang = self.parent.Loc.ang - math.pi/2 + ANG_PADDING
                self.max_ang = self.parent.Loc.ang + math.pi/2 - ANG_PADDING
            self.min_ang = (2*math.pi + self.min_ang) % (2*math.pi)
            self.max_ang = (2*math.pi + self.max_ang) % (2*math.pi)
        super().Update()

#%% if__name__==__main__

if __name__ == '__main__':
    setng = {'empty_dock': True, 'double_let':True, 'vow_splt': True}
    text = input('Type in text to translate:')
    if text == "":
    	text = "Hello world"
    M = Sentence((0,0),C_SIZE/2 - PADDING,9,text.lower())
    D = M.Generate()
    
