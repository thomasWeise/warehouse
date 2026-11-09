[![build](https://github.com/thomasWeise/warehouse/actions/workflows/build.yml/badge.svg)](https://github.com/thomasWeise/warehouse/actions/workflows/build.yml)
[![coverage report](https://shields.io/badge/pytest-coverage-009000)](https://thomasweise.github.io/warehouse/tc/index.html)
[![https://thomasweise.github.io](https://shields.io/badge/home-thomasweise.github.io-009000)](https://thomasweise.github.io)


# warehouse: A warehouse simulator

- [Introduction](#1-introduction)
- [Scenario](#2-scenario)
- [Input Data](#3-input-data)
    - [Bin Types](#31-bin-types)
    - [Parts](#32-parts)
    - [Products](#33-products)
    - [Checkpoints](#34-checkpoints)
- [License](#4-license)
- [Contact](#5-contact)


## 1. Introduction

This is a warehouse simulator.
It tries to simulate what is going on in a warehouse that directly feeds an assembly line.
The assembly line assembles products and therefore needs parts.
The parts come from the warehouse.
The warehouse needs to be replenished to not run out of parts.
We want to avoid [running out of parts](https://thomasweise.github.io/warehouse/warehouse.event.html#warehouse.event.storage.Understock) but we also want to avoid that the warehouse is [overflowing](https://thomasweise.github.io/warehouse/warehouse.event.html#warehouse.event.storage.OverstockIn).

## 2. The Scenario

### 2.1. The Warehouse Side
The warehouse has bins to store the parts that are required by the assembly line.
Each bin has [type](#31-bin-types).
A bin type can be random or not.
In random bins, parts of different types can be stored.
Other bin types are specific, meaning that only one type of parts can be stored in them.
Each bin always stores exactly zero or one packages of a given part.
We know how many packages a bin type can store.

The main task of the warehouse is to store and supply [parts](#32-parts).
Parts come in packages into the warehouse and also leave in packages.
Each package occupies exactly one bin.
A package may include multiple units of a given part&nbsp;(but always only of one part type).
Replenishment rules work with units of parts, though.
For each part, we thus also know how many units are contained in one package.


### 2.2. The Assembly Line Side
On the assembly line, units of different [products](#33-products) are processed continuously.
These products pass by [checkpoints](#34-checkpoints).
When product units pass by checkpoints, they are registered.
Only during these moments, the progress of the assembly line becomes visible to the supervising personell.

Each product has a bill of materials, i.e., the list of per-product [demands](#35-demands-the-bill-of-material) for parts.
Each demand is triggered at a certain check point and specifies how many units of which part are needed.
Optionally, it can also specify how long after the product unit passes the checkpoint this need arises.


### 2.3. The Rule Side
The simulation supports two kinds of rules.

[Min/Max-Rules](#36-minmax-rules) allow for automated replenishment of parts if they drop below a certain amount.
A Min/Max-Rule specifies three things:

- The [part](#32-parts) for which it applies,
- the minimum number of units of that part that we always want to have in the warehouse, and
- the level to which we will replenish the warehouse if the stock level falls under the minimum.

If the stock level ever falls under the minimum, we will order at least one  new package of material.
We will basically compute `(units in warehouse + units on the way)` and divide this by the units per package.
This value is rounded *down*, but never below 1.
Then this gives us the number of packages that we have to order to replenish the warehouse.

*Notice* that `units on the way` *only* considers units ordered by the Min/Max-Rule itself.

*Notice* further that, while the rule considers amount of part *units*, it always orders *packages*.
Only *packages* can enter and leave the warehouse.

Min/Max-Rules are checked every two minutes by default, starting immediately
at the beginning of the work day.


## 3. Input Data
The input data of a simulation is stored in multiple `csv` files inside one folder.

Each datatype has an associated `csv` file.
Some of the files are optional, some are required.
Columns in the files are separated by&nbsp;`;`.
Each file has a first row with column headers.
The order of columns does not matter, i.e., you can provide the columns in any order you wish.

Several example datasets are given in the folder [`examples/instances`](https://github.com/thomasWeise/warehouse/tree/main/examples/instances) of this repository.


### 3.1. Bin Types
For *each [bin type](https://thomasweise.github.io/warehouse/warehouse.instance.html#module-warehouse.instance.bin_type),* we need the following information:

1. The name of the bin type.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for bin types, you may just name them "bin-type-1", "bin-type-2", &hellip; 
2. How many bins of that type exist, i.e., how many packages we can store into the bins of this type in total.
3. Whether this is a random bin or not.

This data is stored in the file&nbsp;`bin_types.csv`.
Each row represents one bin type.
Such a file is required, i.e., you cannot simulate the warehouse without this information.
It could look like this:

```text
name;packages;is_random
rack_1;100;T
rack_2;500;T
rack_3;300;T
floor_1;200;F
floor_2;50;F
floor_3;25;F
```

*Notice:* The first row contains the column names.
These names are important and must not be changed.
Here, `name`&nbsp;is the unique name of the bin type.
`packages`&nbsp;stands for the number of packages we can store in total, i.e., it is also the number of bins of that type.
`is_random`&nbsp;tells us whether the bins of this type are random bins&nbsp;(`T`) or part-specific bins&nbsp;(`F`).

In the above example, `rack_1` is a random bin type, i.e., can store multiple different types of parts.
We got 100&nbsp;bins of type&nbsp;`rack_1`.
Which part types can be stored in the bin is then specified in [`parts.csv`](#32-parts) in the next section.

`floor_1`, on the other hand, is a fixed/part-specific bin type.
We have space for 200&nbsp;packages in it, but can only store exactly one type of part in it.
In [`parts.csv`](#32-parts) in the next section, you can see that this will be parts of type&nbsp;`J`.


### 3.2. Parts
For *each [part](https://thomasweise.github.io/warehouse/warehouse.instance.html#module-warehouse.instance.part),* we store the following information.

1. The name of the part.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for parts, you may just name them "part-1", "part-2", &hellip;
2. The name of the [bin type](#31-bin-types) which is used for packages of this part.
   This means that packages of this part must always be stored into bins of this part.
   Parts always enter and leave the warehouse in *packages*.
   Each package will occupy exactly one bin of the bin type of the part.
   Each part can be stored only into exactly one type of bins.
3. While our warehouse processes only *packages* of parts, the replenishment rules deal with part *units*, not *packages*.
   So, for each part, we also store how many units will be contained in one package.
   We assume that all packages of this part contain exactly this number of units.
   We do not simulate half-full packages or packages with missing/removed parts.

This data is stored in the file&nbsp;`parts.csv`.
Each row represents one part.
Such a file is required, i.e., you cannot simulate the warehouse without this information.
It could look like this:

```text
name;bin_type;units_per_package
A;rack_1;3
B;rack_1;2
C;rack_1;1
D;rack_1;4
E;rack_3;5
F;rack_3;6
G;rack_2;7
H;rack_2;8
I;floor_1;9
J;floor_2;10
K;floor_3;11
```

Here, `name`&nbsp;is the unique name of the part.
`bin_type`&nbsp;identifies the type of bin into which the packages of this part are stored.
You can see that this corresponds to the column `name` in file [`bin_types.csv`](#31-bin-types) back in Section&nbsp;[Bin Types](#31-bin-types).
The column `units_per_package` contains a number presenting the number of units of the part per package.
In the above example, packages with parts of type&nbsp;`A` go into bins of type `rack_1` and each such package contains&nbsp;`3` units of&nbsp;`A`. 


### 3.3. Products
For *each [product](https://thomasweise.github.io/warehouse/warehouse.instance.html#module-warehouse.instance.product),* we store the following information.

1. The name of the checkpoint.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for products, you may just name them "product-1", "product-2", &hellip;

This data is stored in the file&nbsp;`products.csv`.
Each row represents one product.
Such a file is *optional*, i.e., if you do not need products, you can simply not supply it.
This makes sense if you just want to simulate packages going in and out of the warehouse.
The file could look like this:

```text
name
jacket
hat
shoe
```

Here, `name`&nbsp;is the unique name of the product.
In other words, we have three products: `jacket`, `hat`, and `shoe` in our simulation.


### 3.4. Checkpoints
For *each [checkpoint](https://thomasweise.github.io/warehouse/warehouse.instance.html#module-warehouse.instance.checkpoint),* we store the following information.

1. The name of the checkpoint.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for checkpoints, you may just name them "checkpoint-1", "checkpoint-2", &hellip;

This data is stored in the file&nbsp;`checkpoints.csv`.
Each row represents one checkpoint.
Such a file is *optional*, i.e., if you do not need checkpoints, you can simply not supply it.
It could look like this:

```text
name
M1
S1
S2
```

Here, `name`&nbsp;is the unique name of the checkpoint.
In other words, we have three checkpoints in our simulation:&nbsp;`M1`, `S1`, and&nbsp;`S2`.


### 3.5. Demands: The Bill of Material
Each [product](#33-products) requires a set of parts to manufacture.
All such requirements form the bill of material.
Each item of this list is here called a [demand](https://thomasweise.github.io/warehouse/warehouse.instance.html#module-warehouse.instance.demand).
For *each demand,* we store the following information.

1. The name of the [product](#33-products) which requires the parts.
   This name references a name given in `products.csv`.
2. The name of the [checkpoint](#34-checkpoints) when the demand is triggered.
   This name references a name given in `checkpoints.csv`.
3. The name of the [part](#32-parts) that is needed.
   This name references a name given in `parts.csv`.
4. The amount of units of the part that are needed.
   If omitted, it is assumed that 1&nbsp;unit is needed.
   *Notice:*&nbsp;The amount is given in *units*, not in *packages*.
5. If the product unit passes the check point, we might not immediately need this part.
   It could be that, say, an hour passes before we actually need it.
   Therefore, we can *optionally* specify the amount of time (`delay`) *after* the checkpoint when the parts are required.
   The format is `hours:minutes[:seconds]`, i.e., the `seconds` part is optional.
   If this information is not supplied, it is assumed that the parts are needed immediately.

This data is stored in the file&nbsp;`demands.csv`.
Each row represents one demand.
Such a file is *optional*, i.e., if you do not need demands, you can simply not supply it.
However, if this file is supplied, then you **must** also supply `checkpoints.csv` and `products.csv`.
The file could look like this:

```text
checkpoint;product;part;delay;units
M1;jacket;A;00:25;3
M1;jacket;B;00:45;4
S1;jacket;C;00:35;5
S2;jacket;D;00:40;6
M1;hat;E
```

Here, `checkpoint` gives the name of the [checkpoint](#34-checkpoints), `product` gives the name of the [product](#33-products), `part` is the name of the [part](#32-parts), and `units` specifies the number of units of the part that is required by one unit of the product after passing the checkpoint.
`delay`&nbsp;optionally defines a delay when this requirement arises. 

In the example, you can see that, if a `jacket` passes checkpoint `M1`, then the need for `3`&nbsp;units of part&nbs;`A` arise exactly 25&nbsp;minutes later.
Also, `4`&nbsp;units of product&nbsp;`B` will be needed `45`&nbsp;minutes after passing checkpoint&nbsp;`M1`.
The last line tells us that, if a unit of `hat` passes checkpoint&nbsp;`M1`, we will need part&nbsp;`E`.
Since neither a delay nor an amount for part&nbsp;`E` is supplied, the system will assume that `1`&nbsp;unit is required immediately, i.e., after 0&nbsp;seconds.

The column `delay` is optional, but it has one good use case:
It allows the simulation to automatically generate requests to the warehouse.
Normally, we can supply the requests to deliver the warehouse manually, in the `events.csv` list.
However, if we do *know* when the parts are actually needed, then we can simply let the system generate the requests accordingly.
This feature can also be turned on and off separately.
If you supply the requests as part of scenario data, then we turn this feature off and can also simply omit the `delay` column here.


### 3.6. Min/Max-Rules
For each [Min/Max-Rule](https://thomasweise.github.io/warehouse/warehouse.rule.html#warehouse.rule.minmax_rule.MinMaxRule), we store the following information:

1. The name of the rule.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for Min/Max-Rules, you may just name them "MM-1", "MM-2", &hellip;
2. The name of the [part](#32-parts) which is managed by the rule
   This name references a name given in `parts.csv`.
3. The "minimum" amount of *units* of the part we want to have in the warehouse.
   If the amount of units in the warehouse<sup>1</sup> drops *below* this limit, we order new packages.   
4. The "maximum" amount of *units*, i.e., the level to which we will replenish the warehouse by ordering new units.
5. The delay of the effect, i.e., how long it takes after ordering until the parts arrive.

**<sup>1</sup>** The amount of units in the warehouse includes packages that have been ordered by the rule and are currently on the way.
The rule only has knowledge of packages that it ordered by itself.
It has no information about what other rules may have done.

The rules trigger based on the amounts of units in the warehouse, but always order packages.
Min/Max-Rules are checked every two minutes by default.

This data is stored in the file&nbsp;`minmax_rules.csv`.
Each row represents one Min/Max-Rule.
Such a file is *optional*, i.e., if you do not need Min/Max-Rules, you can simply not supply it.
The file could look like this:

```text
name;part;minimum_units;maximum_units;effect_delay
min_A;A;90;180;00:150
min_B;B;80;180;1:40
```

The column `name` represents the name of the rule.
`part` identifies a part name from [`parts.csv`](#32-parts).
`minimum_units` is the lower limit of the amount of units of the part we need in the warehouse.
`maximum_units` is the level to which we will replenish the warehouse once the rule is triggered.
`effect_delay` is the delay until packages ordered by this rule will arrive.
It is specified in the format `hours:minutes[:seconds]`, i.e., the `seconds` part is optional.

From the example given above, we see that two Min/Max-Rules exist.
The rule with the name `min_A` says that there should never be less than 90&nbsp;units of part&nbsp;`A` in the warehouse.
If the stock level of that part drops *below* 90, e.g., to 87, then the rule will trigger.
It will then order as many packages as needed to get the stocklevel up to 180&nbsp;units.
These freshly ordered packages will arrive after 150&nbsp;minutes.

For part&nbsp;`B`, the second rule (named `min_B`) observes that there never shall be less than 80&nbsp;units.
If the stock level drops below 80, say to 79, then it orders as many packages as needed to get the stock level for part&nbsp;`B` back up to&nbsp;180.
These packages will then arrive after 1&nbsp;hour and 40&nbsp;minutes.


## 4. License
Copyright (C) 2026 [Thomas Weise](https://thomasweise.github.io)  (汤卫思教授)

Dr. [Thomas Weise](https://thomasweise.github.io)  (see [Contact](#3-contact)) holds the copyright of this package.
`warehouse` is provided to the public as open source software under the [GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007](https://thomasweise.github.io/warehouse/LICENSE.html).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Please visit the [contributions guidelines](https://thomasweise.github.io/warehouse/CONTRIBUTING_md.html) for `moptipy` if you would like to contribute to our package.
If you have any concerns regarding security, please visit our [security policy](https://thomasweise.github.io/warehouse/SECURITY_md.html).


## 5. Contact
If you have any questions or suggestions, please contact
Prof. Dr. [Thomas Weise](https://thomasweise.github.io) (汤卫思教授) of the 
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/aibd)) at
[Hefei University](http://www.hfuu.edu.cn/english) ([合肥大学](http://www.hfuu.edu.cn)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
