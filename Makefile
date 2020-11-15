dir_name=-g
export dir_name
get-solstorm-results:
	scp -r anderhva@solstorm-login.iot.ntnu.no:/storage/users/anderhva/$(dir_name) /Users/andersvandvik/Repositories/project-thesis/solstorm/$(dir_name)