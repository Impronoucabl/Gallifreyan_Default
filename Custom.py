# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 02:17:41 2022

@author: Impronoucabl

This file is where you can easily add in or modify your own functions into 
the translator, for simple generational & aesthetic changes.


"""
import math

def Divot_Dist_func(Wrd_cir, lett_cir):
    divot_dist = Wrd_cir.outer_rad - lett_cir.inner_rad + 1
    circ_dist = Wrd_cir.inner_rad - lett_cir.outer_rad - 2*lett_cir.thickness
    semi_dist = Wrd_cir.outer_rad
    return (divot_dist, circ_dist, semi_dist)
def DotSize_func(Syllable):
    Radius= Syllable.radius
    return Radius/4, 0.5*Radius
def Semi_Spread_func(Syl):
    num = Syl.prime.cType[2]
    if num == 1:
        spread = (1,)
    elif num == 2:
        spread = (5/6, 7/6)
    elif num == 3:
        spread = (3/5, 1, 7/5)
    spread = [(n - 1) for n in spread]
    return tuple(map(lambda ang: (1+ang)*math.pi, spread)) 
def Init_Dist_func(radius, num):
    if num == 1:
        return 0
    else:
        return radius*(0.3 + 0.05*(num))
def Init_Spread_func(num):
    spread = []
    for n in range(num):
        spread.append(n*math.pi*2/num)
    return spread
def Init_Rad_func(radius, num):
    if num > 2:
        return radius/(math.sqrt(num + 2))
    else:
        return radius/(num)
    
def Node_pair_Dash(inst):
    node_remain = inst.spare_dash_nodes.copy()
    for node1 in node_remain:
        if node1.pair is not None:
            continue
        for node2 in node_remain:
            if node2.pair is not None or node2.parent is node1.parent:
                continue
            if node2.parent.parent is node1.parent.parent:
                continue
            Check1 = node1.Node_check(node2)
            if Check1:
                node1.pair_node(node2)
                inst.spare_dash_nodes.remove(node1)
                inst.spare_dash_nodes.remove(node2)
                break
            
def Node_pair_Split_1(inst, All = False):
        node_remain = inst.spare_dash_nodes.copy()
        Found = False
        for node1 in node_remain:
            if node1.pair is not None:
                continue
            ang_set = set()
            half = node1.min_ang + node1.max_ang/2
            if (2*half)%(2*math.pi) > 0:
                ang_set.add(half)
            twins = []
            if node1.parent.parent.docked:
                for kids in inst.children:
                    if node1.parent.parent in kids.Attachments:
                        for dad in kids.Attachments:
                            if dad is node1.parent.parent:
                                continue
                            twins += dad.prime.children
            for siblings in node1.parent.children + twins:
                if siblings in node_remain:
                    continue
                ang_set.add(siblings.Loc.ang + math.pi)
                ang_set.add((siblings.Loc.ang + node1.min_ang)/2)
                ang_set.add((siblings.Loc.ang + node1.max_ang)/2)
                for siblings2 in node1.parent.children:
                    if siblings2 in node_remain or siblings2 is siblings:
                        continue
                    ang_set.add((siblings.Loc.ang + siblings2.Loc.ang)/2)
                    space = abs(siblings.Loc.ang - siblings2.Loc.ang)
                    ang_set.add(siblings.Loc.ang + space)
                    ang_set.add(siblings.Loc.ang - space)
            for angle in ang_set:
                Nangle = (angle + math.pi*2)%(2*math.pi)
                Pangle = (angle + math.pi)%(2*math.pi)
                if node1.angle_check(Nangle):
                    node1.Loc.Set_ang(Nangle)
                    inst.spare_dash_nodes.remove(node1)
                    Found = True
                    break
                if node1.angle_check(Pangle):
                    node1.Loc.Set_ang(Pangle)
                    inst.spare_dash_nodes.remove(node1)
                    Found = True
                    break
            if Found and not All:
                break