# Introduction
kathara-lab-starter is a simple program that requires no extra python dependencies on debian. 
It allows you to declaratively make a starting configuration for your kathara lab using simple and intuitive json files that are meant to be fast to type.

This tool is meant for _speed_ and **simplicity**, so it didn't make sense to include super complex and router-specific configuration options in the json files, since you could just type those in the appropriate configuration files.
You should just use this to get started quickly, the json file structure is meant to avoid repetitions so there's less room for typing errors and it's easier to check.

After generating the starting lab, you should go in the lab and make the final adjustments yourself.

# How to use

First, clone this repo and cd into it.
```shell
git clone https://github.com/BuonHobo/kathara-lab-starter
cd kathara-lab-starter
```
Then, you can copy the [config](config) directory, which is where you will write your json files.
```shell
cp -r config my-config
```
Now you can delete the json files related to protocols that you don't need. Then you can start editing the ones you need by inserting your own data.
The files are intuitive, but I would like to write a documentation for them if anyone's interested.

Finally, generate your lab
```shell
python main.py my-config my-lab
```
This is obviously not ideal, but it works for now...

# How to add a protocol

This tool is meant to be easy to extend. For now, it's easy to add a new protocol by implementing [these interfaces](daemon/classes.py).

DaemonParser is the class that reads information from the json file and uses it to build a Daemon with all of the domain information.
A Deamon can add itself to a router using the `Daemon.add_router(Router: router)` method.
DaemonConfigurer is the class that will configure each router one at a time, using data about the topology and the domain data stored in Daemon.

After implementing everything, you just need to make sure that the `DaemonParser.merge()` method is called within the `configure_topology()` method in the [wizard.py](topology/wizard.py).
You could add a couple of lines that look like this:
```python
if config.joinpath("dns.json").exists():
    DNSParser(config.joinpath("dns.json")).merge(topology)
```
