if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/vikas-843/MoviesBotv6-main.git /MoviesBotv6-main
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /MoviesBotv6-main
fi
cd /MoviesBotv6-main
pip3 install -U -r requirements.txt
echo "Starting AutoFilterWithStream...."
python3 bot.py
