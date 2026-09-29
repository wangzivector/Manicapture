#include <ros/ros.h>
#include <std_msgs/UInt16MultiArray.h>
#include <dynamic_reconfigure/server.h>
#include <manicapture/machineparamsConfig.h>


class MachineParamServer
{
	public:
	MachineParamServer(ros::NodeHandle* nodehandle);
	void callback_params(manicapture::machineparamsConfig &config, uint32_t level);
	void update_default_state();
	dynamic_reconfigure::Server<manicapture::machineparamsConfig> server;
	int adc_resolution;
	int indicator;
	int sense_delay;
	int grid_type;

	private:
	manicapture::machineparamsConfig params_setting;
	ros::Publisher ptconf_pub;
	ros::Publisher ptgrid_pub;

};

MachineParamServer::MachineParamServer(ros::NodeHandle* nodehandle)
{
	ptconf_pub = nodehandle->advertise<std_msgs::UInt16MultiArray>("/machine_configuration", 1);
	ptgrid_pub = nodehandle->advertise<std_msgs::UInt16MultiArray>("/machine_gridset", 1);
}

void MachineParamServer::update_default_state()
{
	server.getConfigDefault(params_setting);
	// the following line for muting the ROS_WARN for mutex stuff
	if (ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME, ros::console::levels::Error)) { ros::console::notifyLoggerLevelsChanged();}
	server.updateConfig(params_setting);
	if (ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME, ros::console::levels::Info)) { ros::console::notifyLoggerLevelsChanged();}
	while (ros::ok() && ((ptconf_pub.getNumSubscribers() == 0) || (ptgrid_pub.getNumSubscribers() == 0))) 
		ros::Duration(0.01).sleep();
	callback_params(params_setting, 1);
	callback_params(params_setting, 2);
}

void MachineParamServer::callback_params(manicapture::machineparamsConfig &config, uint32_t level)
{
	if(level == 1){
		std_msgs::UInt16MultiArray pt_configuration_msg;
		pt_configuration_msg.data.clear();
		pt_configuration_msg.data.push_back(config.adc_resolution);
		pt_configuration_msg.data.push_back(config.sense_delay);
		pt_configuration_msg.data.push_back(config.update_range);
		pt_configuration_msg.data.push_back(config.sequence);
		pt_configuration_msg.data.push_back(config.hardware);
		pt_configuration_msg.data.push_back(config.indicator);
		ptconf_pub.publish(pt_configuration_msg);
		
		ROS_INFO("update pt_configuration_msg: adc_resolution:%d sense_delay:%d indicator:%d",
				config.adc_resolution, config.sense_delay, config.indicator);
	}
	else if(level == 2){
		std_msgs::UInt16MultiArray pt_gridset_msg;
		pt_gridset_msg.data.clear();
		unsigned short tac0 = config.TACT0?0:8, tac1 = config.TACT1?1:8, tac2 = config.TACT2?2:8, tac3 = config.TACT3?3:8;
		std::vector<unsigned short> USEDTACT = {tac0, tac1, tac2, tac3};
		std::vector<unsigned short> GRID_PAD;
		std::vector<unsigned short> GRID_Dense =  {0, 1, 2, 3, 4, 5, 6, 7};
		std::vector<unsigned short> GRID_Normal = {8, 1, 2, 3, 4, 5, 6, 8};
		std::vector<unsigned short> PAD_Mono =   {4, 8, 8, 8, 8, 8, 8, 8, 8,   4, 8, 8, 8, 8, 8, 8, 8, 8};
		std::vector<unsigned short> PAD_Meidum = {3, 4, 4, 4, 5, 8, 8, 8, 8,   4, 3, 4, 5, 4, 8, 8, 8, 8};
		std::vector<unsigned short> PAD_Full =   {3, 3, 3, 4, 4, 4, 5, 5, 5,   3, 4, 5, 3, 4, 5, 3, 4, 5};
		enum EM_GRIDTYPE {Mono, DenseMedium, DenseFull, NormalMedium, NormalFull};
		switch (config.grid_type)
		{
			case Mono:
				GRID_PAD.insert(GRID_PAD.end(), GRID_Dense.begin(), GRID_Dense.end());
				GRID_PAD.insert(GRID_PAD.end(), PAD_Mono.begin(), PAD_Mono.end());
				break;
			case DenseMedium:
				GRID_PAD.insert(GRID_PAD.end(), GRID_Dense.begin(), GRID_Dense.end());
				GRID_PAD.insert(GRID_PAD.end(), PAD_Meidum.begin(), PAD_Meidum.end());
				break;
			case DenseFull:
				GRID_PAD.insert(GRID_PAD.end(), GRID_Dense.begin(), GRID_Dense.end());
				GRID_PAD.insert(GRID_PAD.end(), PAD_Full.begin(), PAD_Full.end());
				break;
			case NormalMedium:
				GRID_PAD.insert(GRID_PAD.end(), GRID_Normal.begin(), GRID_Normal.end());
				GRID_PAD.insert(GRID_PAD.end(), PAD_Meidum.begin(), PAD_Meidum.end());
				break;
			case NormalFull:
				GRID_PAD.insert(GRID_PAD.end(), GRID_Normal.begin(), GRID_Normal.end());
				GRID_PAD.insert(GRID_PAD.end(), PAD_Full.begin(), PAD_Full.end());
				break;
			default:
				ROS_WARN("Wrong grid pad type for tactile sensing. using default");
				GRID_PAD.insert(GRID_PAD.end(), GRID_Normal.begin(), GRID_Normal.end());
				GRID_PAD.insert(GRID_PAD.end(), PAD_Meidum.begin(), PAD_Meidum.end());
				break;
		}
		pt_gridset_msg.data.insert(pt_gridset_msg.data.end(), USEDTACT.begin(), USEDTACT.end());
		pt_gridset_msg.data.insert(pt_gridset_msg.data.end(), GRID_PAD.begin(), GRID_PAD.end());
		ptgrid_pub.publish(pt_gridset_msg);

		std::stringstream ss;
		ss << "sent";
		// for (uint8_t i = 0; i < USEDTACT.size(); ++i) {ss << USEDTACT[i];ss << ";  ";}
		// for (uint8_t i = 0; i < GRID_PAD.size(); ++i) {ss << GRID_PAD[i];ss << ":";} 
		// for (uint8_t i = 0; i < pt_gridset_msg.data.size(); ++i) {ss << ":" << pt_gridset_msg.data[i];} 
		ROS_WARN("update pt_gridset_msg: mode:%d with full msg be %s.", config.grid_type, ss.str().c_str());
	}
}


int main(int argc, char **argv)
{
	//init ros node
	ros::init(argc, argv, "machine_server");
	ros::NodeHandle n;
	
	MachineParamServer params_base(&n);

	// bind callback with server
    dynamic_reconfigure::Server<manicapture::machineparamsConfig>::CallbackType f_p;
	f_p = boost::bind(&MachineParamServer::callback_params, &params_base, _1, _2);
	params_base.server.setCallback(f_p);
	ROS_WARN("FINISHED CALLBACK SET");
	params_base.update_default_state();
	ROS_WARN("START SPIN");

	ros::spin();
	return 0;
}
