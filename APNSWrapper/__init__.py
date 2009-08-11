# Copyright 2009 Max Klymyshyn, Sonettic
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ssl
import os, sys, struct, base64, socket, datetime


NULL = 'null'

def _doublequote(str):
	"""
	Replace double quotes if it's necessary
	"""
	return str.replace('"', '\\"')
		
def if_else(condition, a, b):
	"""
	It's helper for lambda functions.
	"""
	if condition: return a
	else: return b
	
class APNSTypeError(Exception):
	"""
	This exception raised when you try to add an argument with
	unexpected type.
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class APNSPayloadLengthError(Exception):
	"""
	If length of payload more than 256 (by APNS specification) generate this exception
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class APNSCertificateNotFoundError(Exception):
	"""
	This exception raised when you try to add an argument with
	certificate file but certificate not found.
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
		
class APNSValueError(Exception):
	"""
	This exception raised when you try to add value to method
	which expect concrete type of argument.
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
	
class APNSUndefinedDeviceToken(Exception):
	"""
	This exception raised when you try to send notifications by wrapper
	but one of notification don't have deviceToken.
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
	
	
class APNSConnectionError(Exception):
	"""
	This is a simple exception which generated when
	you can't connect to APNS service or your
	certificate is not valid.
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
		



class APNSAlert(object):	
	"""
	This is an object to generate properly APNS alert object with
	all possible values.
	"""
	def __init__(self):
		self.alertBody = None
		self.actionLocKey = None
		self.locKey = None
		self.locArgs = None
		
	def body(self, alertBody):
		"""
		The text of the alert message.
		"""
		if alertBody and not isinstance(alertBody, str):
			raise APNSValueError, "Unexpected value of argument. It should be string or None."
						
		self.alertBody = alertBody
		return self
		
	def action_loc_key(self, alk = NULL):
		"""
		If a string is specified, displays an alert with two buttons.
		"""
		if alk and not isinstance(alk, str):
			raise APNSValueError, "Unexpected value of argument. It should be string or None."
		
		self.actionLocKey = alk
		return self
		
	def loc_key(self, lk):
		"""
		A key to an alert-message string in a Localizable.strings file for the current 
		localization (which is set by the user's language preference).
		"""
		if lk and not isinstance(lk, str):
			raise APNSValueError, "Unexcpected value of argument. It should be string or None"
		self.locKey = lk
		return self
		
	def loc_args(self, la):
		"""
		Variable string values to appear in place of the format specifiers in loc-key.
		"""
				
		if la and not isinstance(la, (list, tuple)):
			raise APNSValueError, "Unexpected type of argument. It should be list or tuple of strings"
			
		self.locArgs = [ '"%s"' % str(x) for x in la ]
		return self
		
	def _build(self):
		"""
		Build object to JSON Apple Push Notification Service string.
		"""
		
		arguments = []
		if self.alertBody:
			arguments.append('"body":"%s"' % _doublequote(self.alertBody))

		if self.actionLocKey:
			arguments.append('"action-loc-key":"%s"' % _doublequote(self.actionLocKey))

		if self.locKey:
			arguments.append('"loc-key":"%s"' % _doublequote(self.locKey))

		if self.locArgs:
			arguments.append('"loc-args":[%s]' % ",".join(self.locArgs))	
		
		return ",".join(arguments)
	
class APNSProperty(object):
	"""
	This class should describe APNS arguments.
	"""
	name = None
	data = None
	def __init__(self, name = None, data = None):
		if not name or not isinstance(name, str) or len(name) == 0:
			raise APNSValueError, "Name of property argument should be a non-empry string"
			
		if not isinstance(data, (int, str, list, tuple, float)):
			raise APNSValueERror, "Data argument should be string, number, list of tuple"
			
		self.name = name
		self.data = data
	
	
	def _build(self):		
		arguments = []
		name = '"%s":' % self.name
		
		if isinstance(self.data, (int, float)):
			return "%s%s" % (name, str(self.data))
			
		if isinstance(self.data, str):
			return '%s"%s"' % (name, _doublequote(self.data))
		
		if isinstance(self.data, (tuple, list)):
			arguments = map(lambda x: if_else(isinstance(x, str), '"%s"' % _doublequote(str(x)), str(x)), self.data)
			return "%s[%s]" % (name, ",".join(arguments))
			
		return '%s%s' % (name, NULL)
		
class APNSConnection(object):
	"""
	APNSConnection wrap SSL connection to the Apple Push Notification Server.
	"""
	def __init__(self, certificate = None):
		self.socket = None
		self.connectionContext = None
				
		if not os.path.exists(str(certificate)):
			raise APNSCertificateNotFoundError, "Apple Push Notification Service Certificate file %s not found." % str(certificate)
			
		self.certificate = str(certificate)
		
	def connect(self, host, port):	
		"""
		Make connection to the host and port.
		"""
		self.context().connect((host, port))
		return self

	def certificate(self, path):
		self.certificate = path
		return self
				
	def context(self):
		"""
		Initialize SSL context.
		"""
		if self.connectionContext != None:
			return self.connectionContext
			
		self.socket = socket.socket()
		self.connectionContext = ssl.wrap_socket(
					self.socket, 
					ssl_version = ssl.PROTOCOL_SSLv3, 
					certfile = self.certificate
				)
		
		return self.connectionContext
		
	def close(self):
		"""
		Close connection.
		"""
		self.context().close()
		self.socket.close()

class APNSNotificationWrapper(object):
	"""
	This object wrap a list of APNS tuples. You should use
	.append method to add notifications to the list. By usint
	method .notify() all notification will send to the APNS server.
	"""
	sandbox = True
	apnsHost = 'gateway.push.apple.com'
	apnsSandboxHost = 'gateway.sandbox.push.apple.com'
	apnsPort = 2195
	payloads = None
	connection = None
	
	def __init__(self, certificate = None, sandbox = True):
		self.connection = APNSConnection(certificate)
		self.sandbox = sandbox
		self.payloads = []
		
	def append(self, payload = None):
		if not isinstance(payload, APNSNotification):
			raise APNSTypeError, "Unexpected argument type. Argument should be an instance of APNSNotification object"
		self.payloads.append(payload)
		
	def notify(self):
		"""
		Send nofification to APNS:
			1) prepare all internal variables to APNS Payout JSON
			2) make connection to APNS server and send notification
		"""
		payloads = [o.payload() for o in self.payloads]
		payloadsLen = sum([len(p) for p in payloads])		
		messages = []
		offset = 0
		
		if len(payloads) == 0:
			return False
		
		for p in payloads:
			plen = len(p)
			messages.append(struct.pack('%ds' % plen, p))
			offset += plen

		# TODO: make it more correctly
		message = "".join(messages)
				
		apnsConnection = self.connection
						
		if self.sandbox != True:
			apnsHost = self.apnsHost
		else:
			apnsHost = self.apnsSandboxHost
		
		apnsConnection.connect(apnsHost, self.apnsPort)
		connectionContext = apnsConnection.context()
		
		connectionContext.write(message)

		apnsConnection.close()
		
		return True
		
class APNSNotification(object):
	"""
	APNSNotificationWrapper wrap Apple Push Notification Service into 
	python object.
	"""
	
	command = 0
	badge = None
	sound = None
	alert = None
	
	deviceToken = None
	
	maxPayloadLength = 256
	deviceTokenLength = 32

	properties = None
	
	def __init__(self):
		"""
		Initialization of the APNSNotificationWrapper object.
		"""
		self.properties = []
		self.badgeValue = None
		self.soundValue = None
		self.alertObject = None
		self.deviceToken = None		

	
	def token(self, token):
		"""
		Add deviceToken in binary format.
		"""
		self.deviceToken = token
		return self
				
	def tokenBase64(self, encodedToken):
		"""
		Add deviceToken as base64 encoded string (not binary)
		"""
		self.deviceToken = base64.standard_b64decode(encodedToken)
		return self
		
	def badge(self, num = None):
		"""
		Add badge to the notification. If argument is None (by default it is None)
		badge will be disabled.
		"""
		if num == None:
			self.badgeValue = None
			return self
			
		if not isinstance(num, int):
			raise APNSValueError, "Badge argument must be a number"
		self.badgeValue = num
		return self
				
	def sound(self, sound = 'default'):
		"""
		Add a custom sound to the noficitaion. By defailt it is default sound ('default')
		"""
		if sound == None:
			self.soundValue = None
			return self
		self.soundValue = str(sound)
		return self
			
	def alert(self, alert = None):
		"""
		Add an alert to the Wrapper. It should be string or APNSAlert object instance.
		"""
		if not isinstance(alert, str) and not isinstance(alert, APNSAlert):
			raise APNSTypeError, "Wrong type of alert argument. Argument should be String or an instance of APNSAlert object"
		self.alertObject = alert
		return self
	
	def appendProperty(self, *args):
		"""
		Add a custom property to list of properties.
		"""
		for prop in args:
			if not isinstance(prop, APNSProperty):
				raise APNSTypeError, "Wrong type of argument. Argument should be an instance of APNSProperty object"
			self.properties.append(prop)
		return self
	
	def clearProperties(self):
		"""
		Clear list of properties.
		"""
		self.properties = None	
		
	def _build(self):
		"""
		Build all notifications items to one string.
		"""
		keys = []
		apsKeys = []
		if self.soundValue:
			apsKeys.append('"sound":"%s"' % _doublequote(self.soundValue))
			
		if self.badgeValue:
			apsKeys.append('"badge":%d' % int(self.badgeValue))
		
		if self.alertObject != None:
			alertArgument = ""
			if isinstance(self.alertObject, str):
				alertArgument = _doublequote(self.alertObject)					
			elif isinstance(self.alertObject, APNSAlert):
				alertArgument = self.alertObject._build()
			apsKeys.append('"alert":{%s}' % alertArgument)
		
		keys.append('"aps":{%s}' % ",".join(apsKeys))
		
		# prepare properties
		for property in self.properties:
			keys.append(property._build())
		
		payload = "{%s}" % ",".join(keys)
		
		if len(payload) > self.maxPayloadLength:
			raise APNSPayloadLengthError, "Length of Payload more than %d bytes." % self.maxPayloadLength

		return payload
			
	def payload(self):
		if self.deviceToken == None:
			raise APNSUndefinedDeviceToken, "You forget to set deviceToken in your notification."
			
		payload = self._build()
		payloadLength = len(payload)
		tokenLength = len(self.deviceToken)
		tokenFormat = "s" * tokenLength
		payloadFormat = "s" * payloadLength
		
		apnsPackFormat = "ch" + str(tokenLength) + "sh" + str(payloadLength) + "s"
		
		# build notification message in binary format
		return struct.pack(apnsPackFormat, 
									str(self.command), 
									tokenLength, 
									self.deviceToken, 
									payloadLength, 
									payload)
	
			
		

class APNSFeedbackWrapper(object):
	"""
	This object wrap Apple Push Notification Feedback Service tuples.
	Object support for iterations and may work with routine cycles like for.
	"""
	sandbox = True
	apnsHost = 'feedback.push.apple.com'
	apnsSandboxHost = 'feedback.sandbox.push.apple.com'
	apnsPort = 2196
	feedbacks = None
	connection = None
	testingParser = False
	
	blockSize = 1024 # default size of SSL reply block is 1Kb
	feedbackHeaderSize = 6
	
	enlargeRecursionLimit = lambda self: sys.setrecursionlimit(sys.getrecursionlimit() + 100)

	_currentTuple = 0
	_tuplesCount = 0
	
	def __init__(self, certificate = None, sandbox = True):
		self.connection = APNSConnection(certificate)
		self.sandbox = sandbox
		self.feedbacks = []
		self._currentTuple = 0
		self._tuplesCount = 0

	def __iter__(self):
		return self
		
	def next(self):
		if self._currentTuple >= self._tuplesCount:
			raise StopIteration

		obj = self.feedbacks[self._currentTuple]
		self._currentTuple += 1
		return obj
		
	def _parse_reply(self, reply):
		flag = True
		offset = 0
		while(flag):
			try:
				feedbackTime, tokenLength = struct.unpack_from('!lh', reply, offset)
				deviceToken = struct.unpack_from('%ds' % tokenLength, reply, offset + 6)[0]
				offset += 6 + len(deviceToken)
				
				self._append(feedbackTime, deviceToken)				
			except:
				flag = False
		
	def tuples(self):
		"""
		This method return a list with all received deviceTokens:
		( datetime, deviceToken )
		"""
		return self.feedbacks
	
	def _append(self, fTime, token):
		self.feedbacks.append((datetime.datetime.fromtimestamp(fTime), token))
		self._tuplesCount = len(self.feedbacks)
	
	def _parseHeader(self, Buff):
		"""
		Parse header of Feedback Service tuple.
		Format of Buff is |xxxx|yy|zzzzzzzz|
			where:
				x is time_t (UNIXTIME, long, 4 bytes)
				y is length of z (two bytes)
				z is device token
		"""
		try:
			feedbackTime, tokenLength = struct.unpack_from('!lh', Buff, 0)
			if Buff >= self.feedbackHeaderSize + tokenLength:
				recoursiveInvoke = lambda: self._parseTuple(feedbackTime, tokenLength, Buff[self.feedbackHeaderSize:])
				
				# enlarge recursion limit if it is exceeded				
				try:
					return recoursiveInvoke()
				except RuntimeError:
					self.enlargeRecursionLimit()
					return recoursiveInvoke()
			else:
				return Buff
		except:
			return Buff

	def _parseTuple(self, tTime, tLen, Buff):
		"""
		Get body by length tLen of current Feedback Service tuple.
		If body length is equal to tLen than append new
		tuple item and recoursive parse next item.
		
		"""
		try:
			token = struct.unpack_from('!%ds' % tLen, Buff, 0)[0]
			self._append(tTime, token)
		except:
			pass
		
		recurrenceInvoke = lambda: self._parseHeader(Buff[tLen:])
		# enlarge recursion limit if it is exceeded
		try:
			return recurrenceInvoke()
		except RuntimeError:
			self.enlargeRecursionLimit()
			return recurrenceInvoke()

	def _testFeedbackFile(self):
		fh = open('feedbackSampleTuple.dat', 'r')
		return fh
			
	def receive(self):
		"""
		Receive Feedback tuples from APNS:
			1) make connection to APNS server and receive
			2) unpack feedback tuples to arrays			
		"""
								
		apnsConnection = self.connection
						
		if self.sandbox != True:
			apnsHost = self.apnsHost
		else:
			apnsHost = self.apnsSandboxHost
		
		apnsConnection.connect(apnsHost, self.apnsPort)
		connectionContext = apnsConnection.context()
		
		tRest = None
		blockSize = self.blockSize
		
		# replace connectionContext to similar I/O function but work
		# with binary Feedback Service sample file
		if self.testingParser:
			connectionContext = self._testFeedbackFile()
			
		replyBlock = connectionContext.read(blockSize)
		while replyBlock:
			if tRest and len(tRest) > 0:
				# merge previous rest of replyBlock and new
				replyBlock = struct.pack('!%ds%ds' % (len(tRest), len(replyBlock)), tRest, replyBlock)
			tRest = self._parseHeader(replyBlock)
			replyBlock = connectionContext.read(blockSize)
			
		# close sample binary file
		if self.testingParser:
			connectionContext.close()
			
		apnsConnection.close()
		return True		
		

def testAPNSWrapper():
	"""
	Method to testing apns-wrapper module.
	"""
	
	#encoded_token = 'UXVuqtRSEXp1BwSdR+aWaiaVWZ2RfsxgegqIT8Cc9so='
	wrapper = APNSNotificationWrapper('iphone_cert.pem', True)
	
	message = APNSNotification()
	#message.tokenBase64(encoded_token)
	message.token('Qun\xaa\xd4R\x11zu\x07\x04\x9dG\xe6\x96j&\x95Y\x9d\x91~\xcc`z\n\x88O\xc0\x9c\xf6\xca')
	message.badge(5)	
	message.sound()
	
	alert = APNSAlert()
	alert.body("Very important alert message")
	
	alert.loc_key("ALERTMSG")
	
	alert.loc_args(["arg1", "arg2"])
	alert.action_loc_key("OPEN")
	
	message.alert(alert)
	
	# properties wrapper
	property = APNSProperty("acme", (1, "custom string argument"))	
	message.appendProperty(property)
	
	
	wrapper.append(message)
	
	print message._build()
	wrapper.notify()


	#feedback = APNSFeedbackWrapper('iphone_cert.pem', True)
	#feedback.receive()
	
	#print "\n".join(["> " + base64.standard_b64encode(y) for x, y in feedback])
	

	
if __name__ == "__main__":
	testAPNSWrapper()
