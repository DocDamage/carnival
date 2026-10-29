"""Surface destinations and sign faces; angles are relative to the approaching traveller.

0 = ahead, 90 = left, -90 = right. No speculative distances or underwater spoilers.
"""
from pathlib import Path
ROOT=Path(r'F:\Carnival')
LEVEL='L_CarnivalWorldExpansion_Connections_Layout'
TAG='CarnivalWayfinding'
# id, road centre, direction of front-face approach, verge offset, front/back rows
SITES=[
 ('CarnivalHospitalGate',(7800,7800,70),54,350,
  [('HOSPITAL',0),('SLUMS',0)],[('CARNIVAL',0)]),
 ('MansionJunction',(-68820,-83416,602),45,330,
  [('NORTH DOCK',0),('PRISON',0)],[('MANSION',0),('CARNIVAL',0)]),
 ('NorthDock',(-55000,-55000,680),75,320,
  [('NORTH DOCK',90),('PRISON',0)],[('NORTH DOCK',-90),('MANSION',0)]),
 ('PrisonApproach',(-31100,-25800,600),47,320,
  [('PRISON GATE',0),('RESEARCH LAB',90)],[('NORTH DOCK',0),('MANSION',0)]),
 ('PrisonBranches',(-29350,-23800,600),47,300,
  [('EAST DOCK',-45),('HOSPITAL',-45),('SEWERS',45)],
  [('NORTH DOCK',0),('RESEARCH LAB',-90)]),
 ('ResearchLab',(-40000,-10000,600),117,190,
  [('RESEARCH LAB',0)],[('PRISON',0),('NORTH DOCK',0)]),
 ('SewerStairs',(-27000,-19800,600),90,180,
  [('SEWERS',0),('STAIRS DOWN',0)],[('PRISON',0),('RESEARCH LAB',0)]),
 ('EastBoatyard',(70400,19800,655),90,320,
  [('HOSPITAL',0),('BOATYARD',90)],[('PRISON',0),('NORTH DOCK',0)]),
 ('Slums',(42209,65381,323),54,350,
  [('SLUMS',-90),('HOSPITAL',0)],[('SLUMS',90),('CARNIVAL',0)]),
 ('Hospital',(94700,127300,643),50,330,
  [('HOSPITAL',0)],[('EAST DOCK',0),('PRISON',0)]),
]
