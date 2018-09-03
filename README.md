# percy
Scripts for starting permanent, lightweight EC2 instances.  I use them mainly to keep permanent SSH sessions (using `screen`) and for building, pushing and testing Docker images.

### Setup

I use a dedicated EC2 keyfile for this purpose.  I assume you have one already at `~/.aws/percy.pem`.

### Instances and storage

This automates creation of the instance.  Some notes on costs and instance setup as of 9/3/18:

|   | vCPU  |  Mem | Storage | `us-east-1` (spot) [spot per yr] |  `us-east-2` (spot) [spot per yr] |
|---|---|---|---|---|---|
| `t3.micro` | 2  |  1 GiB |  EBS only |  $0.0104 ($0.0031) [$27] | $0.0104 ($0.0031) [$27] |
| `t3.small` | 2  |  2 GiB |  EBS only |  $0.0208 ($0.0063) [$54] | $0.0208 ($0.0063) [$54] |
| `t3.medium` |  2 | 4 GiB  | EBS only  | $0.0416 ($0.0125) [$110] | $0.0416  ($0.0125) [$110] |

(and so on for `t3.large`, `t3.xlarge`, `t3.2xlarge`)

* [Spot pricing snapshot](https://aws.amazon.com/ec2/spot/pricing/)

Since these are going to be used for running containers, they will need some storage.  These instances are EBS-only, so we need to consult the [EBS storage](https://aws.amazon.com/ebs/pricing/) pricing charts.

Main storage types of interest are `gp1` (SSD) and `st1` (HDD):

* `gp1`: `$0.10` per GB month
* `st1`: `$0.045` per GB month

But `st1` volumes must be at least 500 GB.

|   | `gp1` month | `gp1` year  | `st1` month | `st1` year |
|---|---|---|---|---|
| 50 GB | $5  |  $60  |  -  | -  |
| 100 GB | $10  |  $120  |  -  | - |
| 200 GB | $20  |  $240  |  - | - |
| 500 GB | $50  |  $600  | $22.50  | $270 |

So a 100GB-`gp1`-year is about comparable to a `t3.medium`-year at spot prices.

To keep costs low but to have a reasonable set of resources for using Docker, I chose `t3.medium` and 100 GB of `gp2` storage.  See `t3med_100gp2` subdirectory for that `Vagrantfile`.

### `screen`

Make note of the IP of the instance, then add the following to `~/.ssh/config`:

```
Host percy
HostName <ip>
User ec2-user
IdentityFile ~/.aws/percy.pem
```

Add the following to `~/.bash_profile`:

```
alias pe='ssh percy'
alias pes='ssh -t percy screen -r -d '
```

Now after starting a named screen session on `percy` with `screen -S <name>`, connect directly with `pes <name>`.  No need to manually `ssh` to `percy` first.
