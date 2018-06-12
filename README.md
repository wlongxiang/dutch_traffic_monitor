# Dutch high way traffic monitor

## Intro
Traffic on main dutch high ways is being monitored, and some live streaming cameras are
available to public on [www.vid.nl](www.vid.nl).

Some motivations for this project:
 - time series data visualization 
 - dataset for traffic prediction
 - most importantly, for fun

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
4. Finally, run:
```
python car_counter.py 
```

