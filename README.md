## Demo results

![](dutch_traffic_monitor/sample_images/predictions.png?raw=true)

![](dutch_traffic_monitor/sample_images/predictions_day.png?raw=true)

![](dutch_traffic_monitor/sample_images/predictions_night.png?raw=true)

![](dutch_traffic_monitor/sample_images/a9_grafana.png?raw=true)

## Intro
Traffic on main dutch high ways is being monitored, and some live streaming cameras are
available to public on [www.vid.nl](www.vid.nl).

Motivations for this project:
 - **time series data visualization** 
 - **collecting dataset for traffic prediction**
 - **most importantly, for fun!**

Steps:
 - crawl the website mentioned above to get videos clips every certain
amount of time
 - get real time traffic number by running deep learning based object (vehicle) detection algorithms
on video frames
 - visualize the data by using MySQL container for storage and grafana container for making graphs
 

## How to run this code?

1. Spin the enviroment
```
docker-compose up --build
```

2. Run the detection code
```
docker exec dutch_traffic_monitor_pydarknet_1 ./run.sh
```


3. Open you browser and go to [localhost:3000](localhost:3000), log in to
grafana with
 - username: admin
 - password: admin
 
4. After log in, go to settings and add data source, choose MySQL in the dropdown list
 , and fill in the following information, you can ignore the user permission warning for now:
  - Name: A9
  - Type: MySQL
  - Host: mysql:3306
  - Database: traffic
  - User: root
  - Password: mysqladmin 
  
Click "save and test", if you see connection ok, ready to go!

5.  Now you have the data source, go to add a new graph dashboard in grafana, find the metrics tab under edit option of
your graph, choose dada source *A9*, then paste the following query:
```dtd
SELECT
  time as time_sec,
  NbofCars as value
FROM traffic.A9
ORDER BY time ASC
```
Click **Query Inspector** to see if you get response, if yes, go to settings, change
timezone to UTC.

Hooray! Adjust the plot style, change your time range to *Today* or whatever your like to see your data.