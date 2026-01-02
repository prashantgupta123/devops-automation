read -r -p "Enter the environment (prod_ap-south-1) you want to run: " env
set -e

#rm -rf .terraform
if [ "${env}" == "prod_ap-south-1" ] || [ "${env}" == "prod_ap-south-1" ]; then
	terraform init
	terraform fmt --recursive
	terraform workspace list
	terraform workspace select "${env}"
	terraform validate
	terraform destroy
else
	echo "Please enter correct environment"
fi
