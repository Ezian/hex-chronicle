# hex-chronicle
An hex-map generator for exploration sand-box RPG 

## Python version

Python 3.8.10

## Requirements

```sh
pip install python-frontmatter
```

## Usage

```sh
python hexamap.py [files or repositories, allows glob pattern]
```

The script will fetch all files and repository passed as parameters. For each file with a filename formatted like `XXYY-somedescription.md` it will create a hexammap with enough hexagon to contains those defined from the XX,YY coordinate in the filenames.

Moreover, it will retrieve frontmatter metadata to add some features to the terrain polygon.

## Hexagon description example

```md
---
terrain:
    type: heavy_woods

---

# The content doesn't matter now

We only get metadata to draw the map. But the content maybe useful for something else (I don't know, a Hugo website which will host the generate map, for instance ? ;) ) 
```

## The Hexagon concept

```ascii
                                                                      N
       point NO--> o----------o <-- point NE                   NO     |     NE          
                  / \    N   / \                                 \    |    /
                 /   o------o   \                                 \   |   /
                / NO/        \ NE\                                 \  |  /
               /   /          \   \                                 \ | /          
   point O--> <o---o  Zone C   o---o <-- point E          O --------- C --------- E
               \   \          /   /                                 / | \ 
                \ SO\        / SE/                                 /  |  \    
                 \   o------o   /                                 /   |   \   
                  \ /    S   \ /                                 /    |    \  
       point SO--> o----------o <-- point SE                   SO     |     SE
                                                                      S


```

For each hexagon, we can define several points, and zone that can be defined trough their cardinal point (N, E, S, O, NE, SE, NO, SE) and their type (external point, internal point, zone). The center is a specific zone.

It will be used to make easier to draw grid, and coast hexagon where the whole surface of the hexagon is not covered by the same terrain type.

### Zone composition

It is possible to define compound zone, which can also be unambiguously specified with a cardinal point and a number of "atomic" zone:

* `N{3}` is the composition of atomic zone N, NO, NE* 
* `N{2}` doesn't exists since it would be ambiguous between (N, NO) and (N, NE) (same as any `N{2k}`)
* `N{5}` is the composition of atomic zone N, NO, NE, SO, SE
* `O{2}` would be the composition of NO and SO.


With this concept, we can easily compute different subparts of the hexagon and create SVG layer to hide some of them.

### Polygon composition

Each zone can be computed as a polygon of 4 points (2 of the inner hexagon, 2 of the outer). Computing a valid compound zone polygon requires to put all those points in a set, then sort the sequence like that: Outer circle point in trigonometric order (E < NE < NO < O < SO < SE < E, points must be consecutive), inner circle point in reverse-trigonometric order (E < SE < SO < O < NO < NE < E)

## Example of the final map


![It's beautiful](hexgrid-example.svg)

# TODOs

- Refacto : introduce "Hexagon" concept
- hex bicolor (hex we sea coast)
- Roads
- Rivers
- hex icon from description
- securization (markers at borders and number color or font)
- Hex icon from terrain (font awesome ?)
- Fix : zero row or column and Negative row column for hex


## Thanks
 
 Thanks to <https://github.com/toonvandeputte/hexmaker> which give me the base of the algorithm.
