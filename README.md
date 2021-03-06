# Welcome
`quandl` command for Splunk allows import of datasets found on https://www.quandl.com directly into Splunk for further processing and analysis. Gain instant access to 10s of millions of datasets across 100s of unique databases!

This project is hosted on GitHub, see https://github.com/hire-vladimir/SA-quandl

# Install
App installation is simple, and only needs to be present on the search head. Documentation around app installation can be found at http://docs.splunk.com/Documentation/AddOns/released/Overview/Singleserverinstall

# Getting Started
quandl offers many free and paid datasets; some can be accessed anonymously, while others will require an API key. More information regarding obtaining the quandl API key can be found at https://www.quandl.com/docs/api?json#api-keys

*Note:* If a particular static/historic dataset is used in search, it is suggested to create a saved search that will run on a set interval of time, such that outputs of `quandl` command will output to a CSV file to be used as lookup.

## Screenshot
![quandl command for splunk](https://raw.githubusercontent.com/hire-vladimir/SA-quandl/master/static/quandl.gif)
![quandl command for splunk example](https://raw.githubusercontent.com/hire-vladimir/SA-quandl/master/static/quandl_example.png)

## System requirements
The command was tested on Splunk 6.3+ on CentOS Linux 7.1. Splunk python is used, without other dependencies, therefore command *should* work on other Splunk supported platforms.

## Command syntax
`quandl (<options>)* (<auth_key>)? "<quandl_code>"`

## Command arguments (optional)
Command implements arguments listed below. There are two types of arguments for this command, **debug**, **metadata**, **convert_time** that are unique to the command, rest are *quandl API* supported arguments; see full description and usage detail at https://www.quandl.com/docs/api?json#retrieve-data. Command fully supports *quandl v3* API.

When column names such as `['Date', 'Year', 'Month']` are detected, command will attempt to convert time to epoch for use with Splunk's `_time`. If this behavior is not desired, set **convert_time=f** argument.

```debug=<bool> | metadata=<bool> | convert_time=<bool> | auth_token=<quandl_auth_token> | limit=<int> | rows=<int> | column_index=<int> | start_date=<yyyy-mm-dd> | end_date=<yyyy-mm-dd> | order=<asc|desc> | collapse=<none|daily|weekly|monthly|quarterly|annual> | transform=<none|diff|rdiff|cumul|normalize>```

## Examples
* Will pull down "Wiki EOD Stock Prices" dataset, https://www.quandl.com/data/WIKI, for Splunk (SPLK) stock using quandl auth_token of XXXXXXXXXXXXXXXXXXXX; auth_token option overwrites the default configured key.
```
... | quandl auth_token=XXXXXXXXXXXXXXXXXXXX "WIKI/SPLK"
```
* Will pull down *Wiki EOD Stock Prices* dataset, https://www.quandl.com/data/WIKI, for Splunk (SPLK) and Apple (AAPL), starting 2015, with limit of 4 records per stock symbol.
```
... | quandl start_date=2015-01-01 limit=4 "WIKI/(SPLK|AAPL)"
```
* Using the metadata option will return dataset metadata information as described on quandl.com for United States GDP; no data will be returned.
```
... | quandl metadata=true "FRED/USARGDPQDSNAQ"
```
* Using the debug option will enable additional logging on the command to help troubleshoot data set pulls. See troubleshooting section.
```
... | quandl debug=1 "WIKI/SPLK"
```
* It is also possible to pass in Splunk variables from previously executed commands. This example will eval time right "now", and convert it to *YYYY-MM-DD* format, pull down stock data for Splunk for today, write output to CSV file.
```
| localop | stats count | eval my_start_date=strftime(now(), "%Y-%m-%d") | quandl start_date=my_start_date "WIKI/SPLK" | outputlookup append=t my_quandl_stock_data.csv
```
* Pull down historical stock data for Splunk stock, chart low and high price over time.
```
| quandl "WIKI/SPLK" | timechart span=7d latest(High) as price_high latest(Low) AS price_low
```

# Troubleshooting
This command writes log data to *$SPLUNK_HOME/var/log/splunk/quandl.log*, meaning that data is also ingested into Splunk. Magic, I know. Try searching:
```
index=_internal sourcetype=quandl
```

When debug level logging is required, pass in *debug=true* or *debug=1* argument to the command. This will display enhanced logging in Splunk UI and the log file.
```
... | quandl debug=1 "WIKI/SPLK"
```

# Credit
* Genti Zaimi, for the sweet example dashboard

# Legal
* *quandl* is a registered trademark of quandl.com.
* *Splunk* is a registered trademark of Splunk, Inc.
