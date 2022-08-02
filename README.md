# Testing Latency to Totogi Charging Engine from AWS Regions

1. Launch an Amazon Linux EC2 instance in the region. You can generate 6 TPS on a `t4g.small`
2. Setup Python

```shell
sudo yum install git zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel libffi-devel
```

3. Install pyenv

```shell
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
```

4. Add to your .bashrc

```shell
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

5. Install development tools so compiling works

```shell
sudo yum group install "Development Tools"
```

6. Install Python 3.9.13 and create a virtual environment

```shell
pyenv install 3.9.13
pyenv virtualenv 3.9.13 totogi
pyenv global totogi
```

7. Clone this repo

```shell
git clone https://github.com/totogi/latency-test.git
```

8.  Set your username & password in the environment

```shell
export TOTOGI_USERNAME="infra-user@domain.com"
export TOTOGI_PASSWORD="infraPassword"
export TOTOGI_URL="https://Your.NchfUrl"
```

9. Install requirements

```shell
cd latency-test
pip install -r requirements.txt
```

10. Configure test script (lines 15-25)

```python
# The device, account & provider to use in the simulation
device_id = "ede7914e-4055-4484-9652-da46802266c2"
account_id = "ede7914e-4055-4484-9652-da46802266c2"
provider_id = "fc397a41-7bc8-3fa3-971b-2686c0d77c2f"

# The number of N40 Start/Update/Terminate sessions to iterate (sequentially)
num_sessions = 100

# The number of Update calls for each session
updates_per_session = 5
```

11. Run test

```shell
python latency-test.py
```

A log will be produced called `latency-test.log`. The end of the log file contains timing results broken down by transaction type and then summarized across all transactions.

```
New balance = 911768289280
------------------ Start Transactions ----------------------------------------
Number of samples: 1000
Mean: 157.871671269
Max: 495.644331
Median: 154.597347
Percentiles (p80, p95, p99): [158.635027   170.8292183  221.10870209]
-------------------------------------------------------------------------
------------------ Update Transactions ----------------------------------------
Number of samples: 5000
Mean: 156.8224752796
Max: 362.142383
Median: 154.685133
Percentiles (p80, p95, p99): [158.6508194 169.6464562 205.8922071]
-------------------------------------------------------------------------
------------------ Terminate Transactions ----------------------------------------
Number of samples: 1000
Mean: 156.39349924
Max: 470.097886
Median: 154.1608245
Percentiles (p80, p95, p99): [158.474932   166.57138685 200.37811202]
-------------------------------------------------------------------------
------------------ All Transactions ----------------------------------------
Number of samples: 7000
Mean: 156.91107812957145
Max: 495.644331
Median: 154.5955015
Percentiles (p80, p95, p99): [158.603179   169.4915558  206.32103323]
-------------------------------------------------------------------------
Error count: 9
Error rate: 0.0012857142857142856
Start balance = 964102717440, End balance = 911768289280, Delta = 52334428160
Completed 7001 transactions in 1103.08 seconds. (6.35 TPS)
```
