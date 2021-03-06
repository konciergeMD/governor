from boto import sns

# docs: http://boto.readthedocs.org/en/latest/ref/sns.html

class Sns:
	def __init__(self, config, kms):
		self.conn = sns.connect_to_region(config["region"])
		self.arn = kms.decrypt(config["arn"])

	def publish(self, message):
		try:
			self.conn.publish(self.arn, message)
		except Exception, e:
			raise e
