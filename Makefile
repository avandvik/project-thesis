dir_name=-g
export dir_name
get-solstorm-results:
	scp -r anderhva@solstorm-login.iot.ntnu.no:/storage/users/anderhva/$(dir_name) /Users/andersvandvik/Repositories/project-thesis/output/solstorm/$(dir_name)

remove-config-files:
	rm .config_ipynb && rm report/.config_ipynb

upload-instances:
	scp -r /Users/andersvandvik/Repositories/project-thesis/input/run/ anderhva@solstorm-login.iot.ntnu.no:/home/anderhva/project-thesis-lean/input/