"""
[555 Comments]
Your router code and any other helper functions related to router should be written in this file
"""
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import *
from pox.lib.addresses import *
from pox.lib.packet.icmp import *
from pox.lib.packet.ipv4 import *

log = core.getLogger()

"""
[555 Comments]
  Function : router_handler
  Input Parameters:
      rt_object : The router object. This will be initialized in the controller file corresponding to the scenario in __init__
                  function of tutorial class. Any data structures you would like to use for a router should be initialized
                  in the contoller file corresponding to the scenario.
      packet    : The packet that is received from the packet forwarding switch.
      packet_in : The packet_in object that is received from the packet forwarding switch
"""
	

class storeddata:
	def __init__(self,srcip,payload):
		self.srcip = srcip
		self.payload = payload

def router_handler(rt_object, packet, packet_in):
	sourceport = packet_in.in_port
	sourcemac = packet.src
	destinmac = packet.dst
	print("========================================")
	#print(packet)	
	print("A packet from",sourcemac,"try going to",destinmac,"via",sourceport)
	protocol = packet.payload
	print("This is the protocol")
	print(protocol)
	a = packet.find('arp')	
	if (a):
		sourceip = a.protosrc
		destinip = a.protodst
		print("The packet from",sourceip,"to",destinip)
		if (a.opcode == arp.REQUEST):
			print("This is an ARP Request")			
			rt_object.mac_to_port[sourcemac] = sourceport
			rt_object.ip_to_mac[sourceip] = sourcemac
			
			#if this is passed to the router
			if (destinip in rt_object.routermac):
				#now generate an arp reply
				r = arp()
				r.hwtype = a.hwtype
				r.prototype = a.prototype
                		r.hwlen = a.hwlen
                		r.protolen = a.protolen
				r.opcode = arp.REPLY
				r.hwdst = a.hwsrc
				r.hwsrc = rt_object.routermac[destinip]
				r.protodst = sourceip
				r.protosrc = destinip
				e = ethernet(type=packet.type, src=r.hwsrc,dst=a.hwsrc)
				e.payload = r
				print("Sending ARP reply")
				print("Reply source IP",r.protosrc,"source mac",r.hwsrc)
				print("Reply destin IP",r.protodst,"destin mac",r.hwdst)
				msg = of.ofp_packet_out()
				msg.data = e.pack()
				msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
        			msg.in_port = sourceport
				print("Port",sourceport)
        			rt_object.connection.send(msg)
						
				#instruct router to learn how to deal with this ARP request
				#msgarp1 = of.ofp_flow_mod()
				#msgarp1.match = of.ofp_match()
				#msgarp1.match.dl_type = arp.PROTO_TYPE_IP
				
				#if any arp has this distination (a.sourceIP)
				#send it to a.sourceIP like r did
				#print("For the future ARP request to",a.protosrc,"send to port",sourceport)
				#msgarp1.match.nw_dst = a.protosrc 
				#msgarp1.actions.append(of.ofp_action_dl_addr.set_src(r.hwsrc))
				#msgarp1.actions.append(of.ofp_action_dl_addr.set_src(r.hwdst))
				#msgarp1.actions.append(of.ofp_action_output(port = sourceport))
				#rt_object.connection.send(msgarp1)

			#if this is not sent to the router
			else:	 
				# I have recorded it so I should ignore it
	 			return

		elif (a.opcode == arp.REPLY):
			print("This is an ARP Request Reply")
			rt_object.mac_to_port[sourcemac] = sourceport
			rt_object.ip_to_mac[sourceip] = a.hwsrc
			#if this is passed to the router
			if (destinip in rt_object.routermac):
				print("Instruct the router to remember the arp")
				#msgarp2 = of.ofp_flow_mod()
                                #msgarp2.match = of.ofp_match()
                                #msgarp2.match.dl_type = arp.PROTO_TYPE_IP
				#if any arp has this distination (a.sourceIP)
                                #send it to a.sourceIP in the direction of a
                                print("For the future ARP request to",a.protosrc,"send to port",sourceport)
                                #msgarp2.match.nw_dst = sourceip
				#msgarp2.match.dl_dst = sourcemac
				#msgarp2.actions.append(of.ofp_action_output(port = sourceport))
                                #rt_object.connection.send(msgarp2)
				
				#now send the ICMP message
				i = icmp()
				i.type = TYPE_ECHO_REQUEST
				sdata = rt_object.buff[sourceip]

				i.payload = sdata.payload
				
				pip = ipv4()
				pip.protocol = ipv4.ICMP_PROTOCOL
				pip.srcip = sdata.srcip
				pip.dstip = sourceip
				e = ethernet(type=packet.type, src=a.hwdst,dst=a.hwsrc)
                        	e.type = e.IP_TYPE
                        	pip.payload = i
                        	e.payload = pip
				print("Forwarding ICMP request after received ARP")
				print("ICMP request source IP",pip.srcip,"source mac",a.hwdst)
				print("ICMP request destin IP",pip.dstip,"destin mac",a.hwsrc)
                        	msg4 = of.ofp_packet_out()
                        	msg4.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
                        	msg4.data = e.pack()
                        	msg4.in_port = sourceport
				print("Port",sourceport)
                        	rt_object.connection.send(msg4)
					
			else:
				print("Impossibile")
		else:
			return
	
#-------------------------------------------------------	
	if(packet.find("icmp")):
		#if it is sending to the router
		sourceip = protocol.srcip
		destinip = protocol.dstip
		print("The packet from",sourceip,"to",destinip)
		ipv4payload = protocol.payload
		icmppayload = protocol.payload.payload
		if (destinip in rt_object.routermac):
			#writing replies
			i = icmp()
			i.type = TYPE_ECHO_REPLY
			i.payload = icmppayload
			pip = ipv4()
			pip.protocol = ipv4.ICMP_PROTOCOL
			pip.srcip = destinip
			pip.dstip = sourceip
			e = ethernet(type=packet.type, src=destinmac,dst=sourcemac)
			e.type = e.IP_TYPE
			pip.payload = i
			e.payload = pip
			print("Send ICMP reply source IP",pip.srcip,"sourcemac",destinmac)
			print("Send ICMP reply destin IP",pip.dstip,"destinmac",sourcemac)
			msg4 = of.ofp_packet_out()
			msg4.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
			msg4.data = e.pack()
			msg4.in_port = sourceport
			print("Port",sourceport)
			rt_object.connection.send(msg4)
		else:
			# do something
			if (destinip in rt_object.ip_to_mac):
				#forwarding
				print("The destination is already in the table")
				realdestinmac = rt_object.ip_to_mac[destinip]
				i = icmp()
				i.type = ipv4payload.type
				i.payload = icmppayload
				pip = ipv4()
				pip.protocol = ipv4.ICMP_PROTOCOL
				pip.srcip = sourceip
				pip.dstip = destinip
				e = ethernet(type=packet.type, src=sourcemac,dst=realdestinmac)
				e.type = e.IP_TYPE
				pip.payload = i
				e.payload = pip
				print("Forward ICMP request source IP",pip.srcip,"sourcemac",sourcemac)
				print("Forward ICMP request destin IP",pip.dstip,"destinmac",realdestinmac)
				msg4 = of.ofp_packet_out()
                        	msg4.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
                       		msg4.data = e.pack()
                       		msg4.in_port = rt_object.mac_to_port[realdestinmac]
				print("Port",msg4.in_port)
				rt_object.connection.send(msg4)
			else:
				#storage
				sdata = storeddata(sourceip,icmppayload)
				rt_object.buff[destinip] = sdata 	
				# we need to make arp request
				flag = False
				
				rip = IPAddr('0.0.0.0')
				for key in rt_object.routermac:
					#print(rt_object.routermac[key])
					if (rt_object.routermac[key] ==destinmac):
						rip = key
						flag = True
				
				#if (destinip in rt_object.subnet):
				#	flag = True
				if (destinip == IPAddr('8.8.8.8')):
					flag = False
				if (flag):
					print("Helping ICMP request find the host",destinip)
					a = arp()
                                	a.hwtype = arp.HW_TYPE_ETHERNET
                                	a.prototype = arp.PROTO_TYPE_IP
                                	a.hwlen = 6 
                                	a.protolen = 4 
                                	a.opcode = arp.REQUEST
                                	a.hwdst = EthAddr('ff:ff:ff:ff:ff:ff')
                                	a.hwsrc = rt_object.routermac[rip]
                                	a.protosrc = rip 
                                	a.protodst = destinip
                                	e = ethernet(type=ethernet.ARP_TYPE, src=a.hwsrc,dst=a.hwdst)
                                	e.payload = a 
                                	print('Sending ARP request')
                                	print('Request source IP',a.protosrc,'sourcemac',a.hwsrc)
                                	print('Request destin IP',a.protodst,'destinmac',a.hwdst)
                                	msg = of.ofp_packet_out()
                                	msg.data = e.pack()
                                	msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
                               		rt_object.connection.send(msg)
				else:	
					if (ipv4payload.type == TYPE_DEST_UNREACH):
						return
					print("Generate unreachable message")
					i = icmp()
					i.type = TYPE_DEST_UNREACH
					oriIp = packet.find('ipv4')
            				d = oriIp.pack()
            				d = d[:oriIp.hl * 4 + 8]
            				d = struct.pack("!HH", 0, 0) + d
            				i.payload = d
					pip = ipv4()
					pip.protocol = ipv4.ICMP_PROTOCOL
					pip.srcip = destinip
                        		pip.dstip = sourceip
                        		e = ethernet(type=packet.type, src=destinmac,dst=sourcemac)
                        		e.type = e.IP_TYPE
                        		pip.payload = i 
                        		e.payload = pip 
                        		print("Send ICMP unreach source IP",pip.srcip,"sourcemac",destinmac)
                        		print("Send ICMP unreach destin IP",pip.dstip,"destinmac",sourcemac)
                        		msg4 = of.ofp_packet_out()
                        		msg4.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
                        		msg4.data = e.pack()
                        		msg4.in_port = sourceport
                        		print("Port",sourceport)
                        		rt_object.connection.send(msg4)
