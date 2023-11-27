$setup = <<SCRIPT
set -x
sudo DEBIAN_FRONTEND=noninteractive apt-get -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install autoconf curl git parallel python3-pip python3-virtualenv tshark

sudo mkdir -p /opt
sudo curl -sL -o /opt/gcc-arm-none-eabi.tar.bz2 \
    https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.07/gcc-arm-none-eabi-10.3-2021.07-x86_64-linux.tar.bz2
echo "b56ae639d9183c340f065ae114a30202 /opt/gcc-arm-none-eabi.tar.bz2" | md5sum -c && \
    sudo tar -C /opt -jxf /opt/gcc-arm-none-eabi.tar.bz2
sudo curl -sL -o /opt/gcc-xtensa-esp32-elf.tar.gz \
    https://github.com/espressif/crosstool-NG/releases/download/esp-2021r2-patch3/xtensa-esp32-elf-gcc8_4_0-esp-2021r2-patch3-linux-amd64.tar.gz
echo "5c4386fcbbfa3f483555827c414396f1 /opt/gcc-xtensa-esp32-elf.tar.gz" | md5sum -c &&
    sudo tar -C /opt -zxf /opt/gcc-xtensa-esp32-elf.tar.gz &&
set +x

su - vagrant -c "\ 
set -x; \
git clone --recursive https://github.com/anr-bmbf-pivot/Artifacts-CoNEXT23-DoC.git /home/vagrant/Artifacts-CoNEXT23-DoC;
virtualenv /home/vagrant/doc-eval-env; \
. ~/doc-eval-env/bin/activate; \
pip install --upgrade pyserial \
  -r /home/vagrant/Artifacts-CoNEXT23-DoC/03-dns-empirical/collect/requirements.txt \
  -r /home/vagrant/Artifacts-CoNEXT23-DoC/03-dns-empirical/plot/requirements.txt \
  -r /home/vagrant/Artifacts-CoNEXT23-DoC/05-06-evaluation/scripts/exp_ctrl/requirements.txt \
  -r /home/vagrant/Artifacts-CoNEXT23-DoC/05-06-evaluation/scripts/plots/requirements.txt; \
\
echo 'export PATH=\"\\\$PATH:/opt/gcc-arm-none-eabi-10.3-2021.07/bin:/opt/xtensa-esp32-elf/bin\"' >> ~/.bashrc; \
echo '. \"\\\$HOME\"/doc-eval-env/bin/activate' >> ~/.bashrc; \
set +x"
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.define "Artifacts-CoNEXT23-DoC"
  config.vm.box = "generic/ubuntu2204"
  config.vm.provision "shell", inline: $setup
  config.vm.provision :reload

  config.ssh.connect_timeout = 90
end
