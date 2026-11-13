[![build](https://github.com/thomasWeise/warehouse/actions/workflows/build.yml/badge.svg)](https://github.com/thomasWeise/warehouse/actions/workflows/build.yml)
[![coverage report](https://shields.io/badge/pytest-coverage-009000)](https://thomasweise.github.io/warehouse/tc/index.html)
[![https://thomasweise.github.io](https://shields.io/badge/home-thomasweise.github.io-009000)](https://thomasweise.github.io)

# 1. Introduction

This is a warehouse simulator.
It tries to simulate what is going on in a warehouse that directly feeds an assembly line and, in return, is fed by suppliers.
The assembly line assembles products and therefore needs parts.
The parts come from the warehouse.
The warehouse needs to be replenished to not run out of parts.
We want to avoid [running out of parts](./warehouse.event.html#warehouse.event.storage.Understock) but we also want to avoid that the warehouse is [overflowing](./warehouse.event.html#warehouse.event.storage.OverstockIn).


## 1.1. The Structure of this Documentation
In [Section&nbsp;2](#the-scenario), we describe the scenario and how the simulation works in detail.
We explain the components that exist in the real world and how they interact.

In [Section&nbsp;3](#input-data), we give a specification of the data that you can feed into the simulation.
Basically, this input data tells the simulation what things exist and what the human operators or automated systems tell the warehouse to day.
It also specifies rules that guide the warehouses behavior.

We designed a discrete event simulation to simulate the behavior of the warehouse.
Events are both part of the input *and* the output of the simulation.
[Section&nbsp;4](#events-in-the-simulation) describes these event data.

## 1.2. Quick Start Guide to Data
If you want to run our simulation, you basically need the following pieces of data, each of which is described in detail in the following:

1. the [bin types](#bin-types)
2. the [parts](#parts)
3. the [products](#products)
4. the [checkpoints](#checkpoints)
5. the [bill of material](#demands-the-bill-of-material)
6. the [Min/Max-Rules](#minmax-rules)
7. the [JIT-Rules](#jit-rules)
8. the sequence of [input events](#input-events)


# 2. The Scenario

## 2.1. The Warehouse Side
The warehouse has bins to store the parts that are required by the assembly line.
Each bin has [type](#bin-types).
A bin type can be random or not.
In random bins, parts of different types can be stored.
Other bin types are specific, meaning that only one type of parts can be stored in them.
Each bin always stores exactly zero or one packages of a given part.
We know how many packages a bin type can store.

The main task of the warehouse is to store and supply [parts](#parts).
Parts come in packages into the warehouse and also leave in packages.
Each package occupies exactly one bin.
A package may include multiple units of a given part&nbsp;(but always only of one part type).
Replenishment rules work with units of parts, though.
For each part, we thus also know how many units are contained in one package.


## 2.2. The Assembly Line Side
On the assembly line, units of different [products](#products) are processed continuously.
These products pass by [checkpoints](#checkpoints).
When product units pass by checkpoints, they are registered.
Only during these moments, the progress of the assembly line becomes visible to the supervising personell.

Each product has a bill of materials, i.e., the list of per-product [demands](#demands-the-bill-of-material) for parts.
Each demand is triggered at a certain check point and specifies how many units of which part are needed.
Optionally, it can also specify how long after the product unit passes the checkpoint this need arises.


## 2.3. The Rule Side
The simulation supports two kinds of rules.

**[Min/Max-Rules](#minmax-rules)** allow for automated replenishment of parts if they drop below a certain amount.
A Min/Max-Rule specifies three things:

- The [part](#parts) for which it applies,
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

**[JIT-Rules](#jit-rules)**, on the other hand, work with the bill of materials directly.
There can be only one JIT-Rule per [part](#parts).
Whenever a unit of the [product](#products) passes a certain [checkpoint](#checkpoints), the corresponding [demands](#demands-the-bill-of-material) are checked.
If some units of the part for which an JIT-Rule is active are required, then these units are ordered immediately when the rule triggers.

Notice again that we can only order packages, not single units.
JIT-Rules divide the number of required parts by the number of part units per package and *round the result down*.
This means that it is possible that a JIT-Rule triggers, but finds that not enough part units are required to justify ordering a full package.
In this case, no package is ordered.

The rule remembers the "un-ordered" number of parts, though.
These numbers are added up and, as soon as they reach or exceed the part-units-per-package *and* the JIT-Rule is triggered again, the package will be ordered.

JIT-Rules are checked every five minutes.
All the product units pass through any checkpoint are remembered during these intervalls and processed in one sweep.

JIT-Rules do not share any information with Min/Max Rules-and vice versa.
They also ignore the stocklevel of the warehouse:
Regardless of how many units of a given product we already have in the warehouse &mdash; if the rule is triggered, it will order the number of packages needed by the aggregate demand.


## 2.4. Event Side
The warehouse is simulated via a *discrete event simulation*.
This simulation is thus driven by *events*.
Everything that happens is an event.

Something is stored in the warehouse?
That's an event.
Something is taken out of the warehouse?
That's an event.
A product unit passes a checkpoint?
Another event.

Each event happens at a certain date and time.
A part of the input of a simulation are events, such as those mentioned above.
The output the simulation are **also** events.

For example:
A rule triggers?
That's an (output) event.
Some package belonging to a given part is put into a bin?
That's an (output) event.

Actually, all events that go as input into the simulation also come out as output again.
A simulation therefore loads data based on the formats described in [Section&nbsp;3](#input-data).
It also loads a sequence of events following in the format described in [Section&nbsp;4](#events-in-the-simulation).
It then produces output in exactly that same event format.


# 3. Input Data
The input data of a simulation is stored in multiple `csv` files inside one folder.

Each datatype has an associated `csv` file.
Some of the files are optional, some are required.
Columns in the files are separated by&nbsp;`;`.
Each file has a first row with column headers.
The order of columns does not matter, i.e., you can provide the columns in any order you wish.

Several example datasets are given in the folder [`examples/instances`](https://github.com/thomasWeise/warehouse/tree/main/examples/instances) of this repository.


## 3.1. Bin Types
For *each [bin type](./warehouse.instance.html#module-warehouse.instance.bin_type),* we need the following information:

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
Which part types can be stored in the bin is then specified in [`parts.csv`](#parts) in the next section.

`floor_1`, on the other hand, is a fixed/part-specific bin type.
We have space for 200&nbsp;packages in it, but can only store exactly one type of part in it.
In [`parts.csv`](#parts) in the next section, you can see that this will be parts of type&nbsp;`J`.


## 3.2. Parts
For *each [part](./warehouse.instance.html#module-warehouse.instance.part),* we store the following information.

1. The name of the part.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for parts, you may just name them "part-1", "part-2", &hellip;
2. The name of the [bin type](#bin-types) which is used for packages of this part.
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
You can see that this corresponds to the column `name` in file [`bin_types.csv`](#bin-types) back in Section&nbsp;[Bin Types](#bin-types).
The column `units_per_package` contains a number presenting the number of units of the part per package.
In the above example, packages with parts of type&nbsp;`A` go into bins of type `rack_1` and each such package contains&nbsp;`3` units of&nbsp;`A`.


## 3.3. Products
For *each [product](./warehouse.instance.html#module-warehouse.instance.product),* we store the following information.

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


## 3.4. Checkpoints
For *each [checkpoint](./warehouse.instance.html#module-warehouse.instance.checkpoint),* we store the following information.

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


## 3.5. Demands: The Bill of Material
Each [product](#products) requires a set of parts to manufacture.
All such requirements form the bill of material.
Each item of this list is here called a [demand](./warehouse.instance.html#module-warehouse.instance.demand).
For *each demand,* we store the following information.

1. The name of the [product](#products) which requires the parts.
   This name references a name given in `products.csv`.
2. The name of the [checkpoint](#checkpoints) when the demand is triggered.
   This name references a name given in `checkpoints.csv`.
3. The name of the [part](#parts) that is needed.
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

Here, `checkpoint` gives the name of the [checkpoint](#checkpoints), `product` gives the name of the [product](#products), `part` is the name of the [part](#parts), and `units` specifies the number of units of the part that is required by one unit of the product after passing the checkpoint.
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


## 3.6. Min/Max-Rules
For each [Min/Max-Rule](./warehouse.rule.html#warehouse.rule.minmax_rule.MinMaxRule), we store the following information:

1. The name of the rule.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for Min/Max-Rules, you may just name them "MM-1", "MM-2", &hellip;
2. The name of the [part](#parts) which is managed by the rule
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
`part` identifies a part name from [`parts.csv`](#parts).
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


## 3.7. JIT-Rules
For each [JIT-Rule](./warehouse.rule.html#module-warehouse.rule.jit_rule), we store the following information:

1. The name of the rule.
   Names must be unique, i.e., there never can be two objects (bin types, parts, &hellip;) in our simulation with the same name.
   If you do not have reasonable names for JIT-Rules, you may just name them "JR-1", "JR-2", &hellip;
2. The [part](#parts) managed by the rule.
   There can be only one JIT-Rule per part.
   This rule then applies across all products and checkpoints.
3. The delay until the packages ordered by the rule will arrive.

JIT-Rules can only be defined if [products](#products), [checkpoints](#checkpoints), and [demands](#demands-the-bill-of-material) are also given.
They are stored in a file named `jit_rules.csv`.
The file could look like this:

```text
name;part;effect_delay
jit_A;A;02:03
jit_B;B;02:11
jit_C;C;02:07
jit_D;D;02:05

```

The column `name` represents the name of the rule.
`part` identifies a part name from [`parts.csv`](#parts).
`effect_delay` is the delay until packages ordered by this rule will arrive.
It is specified in the format `hours:minutes[:seconds]`, i.e., the `seconds` part is optional.

The first data row of the example above tells us that a JIT-Rule named `jit_A` is watching for parts of type&nbsp;`A`.
If any product passes through a checkpoint and its bill of material says that it requires units of part&nbsp;`A`, then this will trigger this rule.
The rule then checks how many units of part&nbsp;`A` are required in total, by all products that passed through all checkpoints since the rule was checked last time.
If the number of units is high enough so that at least one package is required, the package(s) will immediately be ordered.
They will arrive in the warehouse after 2&nbsp;hours and 3&nbsp;minutes.
If the number is not high enough, it is remembered and added in when the rule is checked next time.

JIT-Rules are checked by default at full five minutes intervals.
They ignore the stocklevel of the warehouse.


# 4. Events in the Simulation
Our simulation is then driven by a stream of [events](./warehouse.event.html#module-warehouse.event).
There are some events that tell the simulation about things that happened or things that the warehouse is supposed to do.
These events are **input** events.
If the warehouse does something or some rule is triggered, that generates **output** events.

Therefore, a stream of **input** events goes into the simulation giving commands to the warehouse.
The simulation simulates what the warehouse does.
This results in more events, the **output** events.
These are then combined with the **input** events and returned to the user.

Therefore, we get an exact picture of what happens, in which order, and why.

The input events of a simulation are stored in a file `events.csv`.
Here we describe this format as well as the types of events that exist.
The output of the simulation can be stored in a file of the same format.

This format has the following columns:

- `time`: The time when the event occurred.
   The format is `year-month-day hour:minute[:second]`, where the seconds are only provided if they are not zero.
- `type`: The type of the event that occurred.
- `part`: The [part type](#parts) involved.
   Some events involve parts, e.g., such that store stuff in the warehouse or retrieve stuff..
   Others don't, and in this case, leave this column empty.
- `packages`: A number of packages involved.
   Events that store packages of parts into the warehouse, retrieve packages, or order packages provide this value.
   Other events that are unrelated to packages omit it.
- `bin_type`: The [bin type](#bin-types).
   This value is provided only for events that store and retrieve things to and from bins.
- `checkpoint`: The name of a [checkpoint](#checkpoints) that was triggered, omitted if the event does not involve checkpoints.
- `product`: The [product](#products) that was involved in the event, omitted if the event is unrelated to products.
- `units`: The number of units of the part or product involved in the event, if any.
- `rule`: The rule that was triggered; either a [Min/Max-Rule](#minmax-rules) or a [JIT-Rule](#jit-rules), or left empty if the event is unrelated to rules.

Here we give an example of how this may look like:

```text
time;type;part;packages;bin_type;checkpoint;product;units;rule
2026-10-15 08:00;start
2026-10-15 08:00;warehouse_in;A;20;;;;60
2026-10-15 08:00;warehouse_in;B;25;;;;50
2026-10-15 08:00;warehouse_in;C;30;;;;30
2026-10-15 08:00;warehouse_in;D;35;;;;140
2026-10-15 08:00;bin_in;A;20;rack_1;;;60
2026-10-15 08:00;bin_in;B;25;rack_1;;;50
2026-10-15 08:00;bin_in;C;30;rack_1;;;30
2026-10-15 08:00;bin_in;D;25;rack_1;;;100
2026-10-15 08:00;overstock_in;D;10;;;;40
2026-10-15 08:00;initialization_complete
2026-10-15 08:00;rule_triggered;A;20;;;;60;min_A
2026-10-15 08:20;checkpoint;;;;M1;jacket;1
2026-10-15 08:20;check_jit
2026-10-15 08:20;rule_triggered;A;1;;;;3;jit_A
2026-10-15 08:20;rule_triggered;B;2;;;;4;jit_B
2026-10-15 08:45;warehouse_demand;A;1;;;;3
2026-10-15 08:45;bin_out;A;1;rack_1;;;3
2026-10-15 08:45;overstock_out;D;1;;;;4
2026-10-15 08:45;bin_in;D;1;rack_1;;;4
2026-10-15 08:49;warehouse_delivered;A;1;;;;3
2026-10-15 08:50;checkpoint;;;;M1;jacket;1
2026-10-15 08:50;check_jit
2026-10-15 08:50;rule_triggered;A;1;;;;3;jit_A
2026-10-15 08:50;rule_triggered;B;2;;;;4;jit_B
2026-10-15 09:05;warehouse_demand;B;2;;;;4
2026-10-15 09:05;bin_out;B;2;rack_1;;;4
2026-10-15 09:05;overstock_out;D;2;;;;8
2026-10-15 09:05;bin_in;D;2;rack_1;;;8
2026-10-15 09:09;warehouse_delivered;B;2;;;;4
....
2026-10-15 13:05;warehouse_demand;B;2;;;;4
2026-10-15 13:05;warehouse_demand;C;20;;;;20
2026-10-15 13:05;bin_out;B;2;rack_1;;;4
2026-10-15 13:05;understock;C;20;;;;20
...
2026-10-15 15:07;end
```

## 4.1. Input Events
The input events describe the situation that requires responses from the warehouse.
For example, they tell us [when](#start) the workday begins, [when](#warehouse_in) we put something into the warehouse, or [when](#warehouse_demand) we want to take something out of the warehouse.
They tell us [when](#checkpoint) a product has passed a checkpoint.

These events then cause the warehouse to [respond](#output-events) by putting stuff into bins, taking things out, encountering over- or understock, and so on.


### 4.1.1. start
This [event](./warehouse.event.html#warehouse.event.time.StartEvent) denotes the start of the simulation.
If you provide it, the `time` value of this event marks the beginning of a work day.
If you do not provide it, then such an event will automatically be generated with the timestamp of the first event in the simulation.

`2026-10-15 08:00;start` means that the workday started on October 15, 2026, at 08:00am.


### 4.1.2. end
This [event](./warehouse.event.html#warehouse.event.time.EndEvent) can be provided to mark the end of the simulation.
No other event can occur after it.
If you do not provide it, it will be generated automatically after the last simulated event.

`2026-10-15 15:07;end` means that the simulation ended after the last event on October 15, 2026, at 15:07(pm).


### 4.1.3. warehouse_in
This [event](./warehouse.event.html#warehouse.event.storage.WarehouseIn) tells us that a certain number of `packages` of the given [`part`](#parts) is stored into the warehouse at a certain time.
The `units` value can be omitted and is automatically computed based on the number of `packages` and the number of units per package for the given part.

You can manually specify such events to express that someone puts something into the warehouse.
In particular, the initial state of the warehouse at the beginning of the workday can be constructed by creating such events for all the items currently stored in the warehouse.

The simulation also generates such events automatically:
If a rule triggers and orders packages of a given part to replenish the warehouse, these will eventually arrive in form of this event.

`2026-10-15 08:00;warehouse_in;A;20;;;;60` means that 20&nbsp;packages of part&nbsp;`A` arrived at the warehouse on October 15, 2026, at 08:00am.
They then need to be stored.
Actually, this event denotes such a warehouse setup situation mentioned above.


### 4.1.4. warehouse_demand
This [event](./warehouse.event.html#warehouse.event.storage.WarehouseDemand) means that the assembly line has asked our warehouse to provide at least one package of a given [part](#parts).

`2026-10-15 08:45;warehouse_demand;A;1;;;;3`, for example, means that 1&nbsp;package of part&nbsp;`A` has been demanded from our warehouse on October 15, 2026, at 08:45am.
One such package here corresponds to 3&nbsp;units of&nbsp;`A`.

Notice that such events can also be automatically generated based on [`checkpoint`](#checkpoint) events and the [bill of material](#demands-the-bill-of-material) *if* this functionality is activated in the simulation.


### 4.1.5. checkpoint
This [event](./warehouse.event.html#warehouse.event.checkpoint.CheckpointEvent) denotes that a certain amount of units of a given [product](#products) has arrived at a certain [checkpoint](#checkpoints).

For example, `2026-10-15 08:20;checkpoint;;;;M1;jacket;1` tells us that 1&nbsp;unit of product&nbsp;`jacket` has been registered at checkpoint&nbsp;`M1` at 08:20 on October 15, 2026.

Checkpoint events can lead to the triggering of [JIT-Rules](#jit-rules) or, if that is activated, of [demands](#demands-the-bill-of-material).


## 4.2. Output Events
Events of this type can never be manually created.
They result from the simulation.


### 4.2.1. warehouse_delivered
Whenever a packages of a given [part](#parts) leaves the warehouse, this [event](./warehouse.event.html#warehouse.event.storage.WarehouseDelivers) is triggered.
This event is the answer to a [`warehouse_demand`](#warehouse_demand) event.
The `warehouse_demand` is either satisfied from the overstock, by taking parts out of the bins, or leads to an [`understock`](#understock) event.
In the latter case, once the understock is resolved because new packages of the part arrive and can be delivered, a `warehouse_delivered` event is triggered as well.

For example `2026-10-15 08:49;warehouse_delivered;A;1;;;;3` means that, on October 15, 2026, at 08:49, 1&nbsp;package of part&nbsp;`A` (corresponding to 3&nbsp;units of part&nbsp;`A`) has left the warehouse.


### 4.2.2. bin_in
This [event](./warehouse.event.html#warehouse.event.bins.BinIn) tells us that a certain number of packages of a [part](#parts) have been placed into bins of the corresponding [type](#31-bin-types
).
Such events are generated as response to [`warehouse_in`](#warehouse_in) events, if empty bins of the required type exist.

`2026-10-15 08:00;bin_in;B;25;rack_1;;;50` means that on October 15, 2026, at 08:00am, 2&nbsp;packages of part&nbsp;`B` were placed into (also 25) bins of type `rack_1`.
This corresponds to 50&nbsp;units.
This units value is automatically computed and otherwise meaningless.


### 4.2.3. bin_out
This [event](./warehouse.event.html#warehouse.event.bins.BinOut) is the opposite of `bin_in` events.
It denotes that a certain number of packages of a [part](#parts) has been taken out of bins of the corresponding [type](#bin-types).
Such events are generated as a response to [`warehouse_demand`](#warehouse_demand) events.

For example, `2026-10-15 08:45;bin_out;A;1;rack_1;;;3` means that, on October 15, 2026 at 08:45am, 1&nbsp;package of part&nbsp;`A` has been taken out of one bin of the type&nbsp;`rack_1`.
(One package here corresponds to 3&nbsp;units).


### 4.2.4. overstock_in
This [event](./warehouse.event.html#warehouse.event.storage.OverstockIn) expresses that a certain amount of packages of a given [part](#parts) could not be placed into bins.
All bins of the required type are occupied.
Therefore, these packages land in the "overstock".
This is one of the things that we would like to avoid.
In other words, such events are generated as a response to [`warehouse_in`](#warehouse_in) events if the amount of empty bins of the required type is insufficient.

For example, `2026-10-15 08:00;overstock_in;D;10;;;;40` means that 10&nbsp;packages of part&nbsp;`D` could not be put into bins on October 15, 2026, 08:00am.
They land in the overstock.
(The value of 40&nbsp;units is computed automatically.)


### 4.2.5. overstock_out
This type of [event](./warehouse.event.html#warehouse.event.storage.OverstockOut) occurs if we remove packages of a given [part](#parts) from the overstock.
The cause of this can either be that some bins of the required [type](#bin-types) have become empty or that a [`warehouse_demand`](#warehouse_demand) has occurred for the part.
Of course, these packages must have arrived in the overstock before due to an [`overstock_in`](#overstock_in) event.

For example, `2026-10-15 08:45;overstock_out;D;1;;;;4` means that on October 15, 2026, at 08:45, 1&nbsp;package of part&nbsp;`D` was removed from the overstock.
(This package corresponds to 4&nbsp;units of part&nbsp;`D`).


### 4.2.6. initialization_complete
After all events that take place right in the first second of the simulation are completed, the [`initialization_complete` event](./warehouse.event.html#warehouse.event.time.InitializationComplete) is generated.
Often, we want to manually trigger some [`warehouse_in`](#warehouse_in) events to build the initial state of the warehouse on that day.
These events will lead to corresponding [`bin_in`](#bin_in) or [`overstock_in`](#overstock_in) events.
After these are all processed, the initialization is over.

`2026-10-15 08:00;initialization_complete`, for example, denotes the end of all setup events (on October 15, 2026, 08:00am).


### 4.2.7. understock
The [worst-case event](./warehouse.event.html#warehouse.event.storage.Understock) for the warehouse is an `understock`.
It happens if a [`warehouse_demand`](#warehouse_demand) is issued but the amount of packages in the warehouse is insufficient to satisfy it.
It therefore tells us how many packages of which [part](#parts) could not be delivered.
(If packages of the part arrive later on, they will directly be sent down the line and directly cause [`warehouse_delivered`](#warehouse_delivered) events.)

For example, `2026-10-15 13:05;understock;C;20;;;;20` means that on October 15, 2026, at 13:05, the warehouse was lacking 20&nbsp;packages of part&nbsp;`C` (corresponding to also 20&nbsp;units of part&nbsp;`C`).


### 4.2.8. rule_triggered
This [event](./warehouse.event.html#warehouse.event.rules.RuleTriggeredEvent) occurs if the condition for triggering a [Min/Max-Rule](#minmax-rules) or [JIT-Rule](#jit-rules) has been met.
The rule was activated and potentially has ordered some new [parts](#parts) to replenish the warehouse.
If so, this will lead to a corresponding [`warehouse_in`](#warehouse_in) event down the line when the ordered package has arrived.

`2026-10-15 08:00;rule_triggered;A;20;;;;60;min_A` denotes that the Min/Max-Rule `min_A` was triggered at 08:00am on October 15, 2026.
It has realized that 20&nbsp;packages of part&nbsp;`A` are needed and ordered them&nbsp;(in order to obain 60 new units of part&nbsp;`A` to replenish our stock).


### 4.2.9. check_minmax
This [event](./warehouse.event.html#warehouse.event.rules.MinMaxRuleCheckEvent) happens when minimum limit of a [Min/Max-Rule](#minmax-rules) has been violated.
Since Min/Max-Rules are only checked every 2&nbsp;minutes by default, the actual rule checking does not happen immediately, but, well, only in two-minute intervals.
This is denoted by this event.
Only after this event, a Min/Max-Rule may actually be triggered.

For example `2026-10-15 12:40;check_minmax` means that the Min/Max-Rules were checked at 12:40 on October 15, 2026.


### 4.2.10. check_jit
This [event](./warehouse.event.html#warehouse.event.rules.JitRuleCheckEvent) happens if a [product](#products) has passed a [checkpoint](#checkpoints) and in its [bill of material](#demands-the-bill-of-material), a [part](#parts) is contained for which a [JIT-Rule](#jit-rules) is defined.
Such events can happen (by default) at most every five Minutes.
When they happen, the [JIT-Rules](#jit-rules) get checked (and may order packages of parts).

`2026-10-15 08:20;check_jit`, for example, means that the JIT-Rules have been checked on October 15, 2026, at 08:20am.
This may then lead to [`rule_trigger`](#rule_triggered) events.


# 5. License
Copyright (C) 2026 [Thomas Weise](https://thomasweise.github.io)  (汤卫思教授)

Dr. [Thomas Weise](https://thomasweise.github.io)  (see [Contact](#contact)) holds the copyright of this package.
`warehouse` is provided to the public as open source software under the [GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007](./LICENSE.html).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Please visit the [contributions guidelines](./CONTRIBUTING_md.html) for `moptipy` if you would like to contribute to our package.
If you have any concerns regarding security, please visit our [security policy](./SECURITY_md.html).


# 6. Contact
If you have any questions or suggestions, please contact
Prof. Dr. [Thomas Weise](https://thomasweise.github.io) (汤卫思教授) of the
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/aibd)) at
[Hefei University](http://www.hfuu.edu.cn/english) ([合肥大学](http://www.hfuu.edu.cn)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
