import multiprocessing

bind = "127.0.0.1:5111"
workers = multiprocessing.cpu_count() * 2 + 1
proc_name = 'cmapi'
max_requests = 1000