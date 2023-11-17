## Jack Everything

An naïve converter that converts music game notes to some kind of jack.

### Usage

```cmd
cd src
python3 main.py -p path_to_your_zip_file [-s splits_in_one_beat] [-o output_dir_path]
```

### Example

```
cd src
python3 main.py -p ../tests/speed10.mcz -s 4
```

```
cd src
python3 main.py -p ../tests/xihaiqingge.mcz -s 2
```

### TODO

Add .osz support 