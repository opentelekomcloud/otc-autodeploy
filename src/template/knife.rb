base_dir = File.join(File.dirname(File.expand_path(__FILE__)), '..')

log_level                :info
log_location             STDOUT
node_name                'admin'
client_key               File.join(base_dir, '.chef', 'admin.pem')
syntax_check_cache_path  File.join(base_dir, '.chef', 'syntax_check_cache')
validation_client_name   "otc-validator"
validation_key           "#{current_dir}/otc.pem"
cache_type               'BasicFile'
cache_options( :path => "#{ENV['HOME']}/.chef/checksums" )
cookbook_path            [File.join(base_dir, 'cookbooks')]

chef_server_url          'https://chef_server_name/organizations/otc'
ssl_ca_file              File.join(base_dir, '.chef', 'ca_certs', 'chef_server_name.crt')
trusted_certs_dir        File.join(base_dir, '.chef', 'ca_certs')

### Knife-OpenStack Access Credentials
#knife[:openstack_username] = "user_name"
#knife[:openstack_password] = "user_password"
#knife[:openstack_tenant] = "user_domain"
#knife[:openstack_auth_url] ="https://iam.eu-de.otc.t-systems.com:443/v3"
