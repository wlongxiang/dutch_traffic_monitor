## Demo results

![](sample_images/predictions.png?raw=true)

![](sample_images/predictions_day.png?raw=true)

![](sample_images/predictions_night.png?raw=true)

![](sample_images/a9_grafana.png?raw=true)

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


It has been developed in macOS, should work without troubles on linux based system. Some tweaks are needed to
make it work on Windows.

1. Make sure you have python 3 installed, python 3.6 is used. Run the following command to install dependencies:

```
pip install -r requirements.txt
```

2. Install Docker, google is your friend.

3. Start the two containers, one for mysql, one for grafana by running the following command under the directory when the **docker-compose.yml** file is:

```
docker-compose up
```
As a result, *mysql_host_dir* will be mapped to */var/lib/mysql/*, *grafana_host_dir* will be mapped to */var/lib/grafana/*, this way
the data collected will persist in your host directory even if the containers
are stopped. You can also change the host directory to your desire by modifying the YAML file and 
rebuild the docker images by running:
```
docker-compose stop
docker-compose up --build
```
Two containers should be up and running now, check it by running:
```
docker-compose ps
```
3. Finally, run:
```
python car_counter.py 
```
You should see a openCV window with cars label, if everything goes well. Time to
visualize!

4. Open you browser and go to [localhost:3000](localhost:3000), log in to
grafana with
 - username: admin
 - password: admin
 
 After log in, go to settings and add data source, choose MySQL in the dropdown list
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