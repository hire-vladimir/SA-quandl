#Welcome
`quandl` command for Splunk allows import of datasets found on quandl.com right into Splunk for further processing ana analysis; via quandl v3 API to return records.

#Install
App installation is simple, and only needs to be present on the search head. Documentation around app installation can be found here [http://docs.splunk.com/Documentation/AddOns/released/Overview/Singleserverinstall](http://docs.splunk.com/Documentation/AddOns/released/Overview/Singleserverinstall)

#Getting Started
quandl offers many free and paid datasets, some can be accessed anonomosly, while others will require an API key. More information regarding obtaining the quandl API key can be found at [https://www.quandl.com/docs/api?json#api-keys](https://www.quandl.com/docs/api?json#api-keys)

*Note:* If a particular static/historic dataset is used used extencively in search, it is recomended to create a saved search that will run on a set inverval of time, such that outputs of '''quandl''' command will be outputed to a CSV file to be used as lookup.

##Command syntax
'''quandl (<options>)* (<auth_key>)? <quandl_code>'''

##Command arguments (optional)
Command implements arguments listed below. There are two types or arguments for this command, *debug* and *metadata* that are unique to the command, the second is quandl supported arguments; see full description and usage detail at https://www.quandl.com/docs/api?json#retrieve-data

'''debug=<bool> | metadata=<bool> | auth_token=<quandl_auth_token> | limit=<int> | rows=<int> | column_index=<int> | start_date=<yyyy-mm-dd> | end_date=<yyyy-mm-dd> | order=<asc|desc> | collapse=<none|daily|weekly|monthly|quarterly|annual> | transform=<none|diff|rdiff|cumul|normalize>'''

##Examples
* will pull down "Wiki EOD Stock Prices" dataset, https://www.quandl.com/data/WIKI, for Splunk (SPLK) stock using quandl auth_token of XXXXXXXXXXXXXXXXXXXX; auth_token option overwrites the default configured key
```
... | quandl auth_token=XXXXXXXXXXXXXXXXXXXX WIKI/SPLK
```
* will pull down "Wiki EOD Stock Prices" dataset, https://www.quandl.com/data/WIKI, for Splunk (SPLK) and Apple (APL), starting 2015, with limit of 4 records per stock symbol
```
... | quandl start_date=2015-01-01 limit=4 "WIKI/(SPLK|APL)"
```
* using metadata option will return dataset metadata information as described on quandl.com for United States GDP; no data will be returned
```
... | quandl metadata=true FRED/USARGDPQDSNAQ
```
* using debug option will enable additional logging on the command to help troubleshoot data set pulls. log is written to UI
```
... | quandl debug=1 "WIKI/SPLK"
```
* it is also possible to pass in Splunk variables from previously derived commands. Will eval time right now, and convert it to YYYY-MM-DD format, pull down stock data for Splunk for today, write output to CSV file.
```
| localop | stats count | eval my_start_date=strftime(now(), "%Y-%m-%d") | quandl start_date=my_start_date "WIKI/SPLK" | outputlookup append=t my_quandl_stock_data.csv
```
* pull down historical stock data for Splunk stock, chart low and high price over time
```
| quandl "WIKI/SPLK" | eval _time=strptime(Date, "%Y-%m-%d") | timechart span=7d latest(High) as price_high latest(Low) AS price_low
```

#Troubleshooting
Command writes log data to *$SPLUNK_HOME/var/log/splunk/quandl.log*, meaning this data is also splunk'ed. Try searching:
'''
'''

When debug level loggin is required, pass in *debug=true* argument to the command. This will display enhance loggin in Splunk UI and the log file.
```
... | quandl debug=1 "WIKI/SPLK"
```

#Legal
* quandl is a registered trademark of quandl.com.
* Splunk is a registered trademark of Splunk, Inc.
