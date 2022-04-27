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

## Example of the final map


![It's beautiful](hexgrid-example.svg)

# TODOs

- hex icon from description
- hex bicolor (hex we sea coast)
- securization (markers at borders and number color or font)
- Roads
- Rivers
- Hex icon from terrain (font awesome ?)
- Fix : zero row or column and Negative row column for hex


## Thanks
 
 Thanks to <https://github.com/toonvandeputte/hexmaker> which give me the base of the algorithm.
