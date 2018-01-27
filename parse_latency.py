#!/usr/bin/python

import sys
import os
import csv

# each latency block size in syslog
# LATENCY_BLOCK_SIZE = 13

#record number in each example
RECORD_NUMBER=5

# index of message in each syslog block
block_offset = {
	"offset_rlc_pdu" 				: 0,
	"offset_bsr_lo_send"			: 1,
	"offset_bsr_ps_rcv"			: 2,
	"offset_mux_req_ps_send"		: 3,
	"offset_mux_req_lo_rcv"		: 4,
	"offset_assemble_mac_pdu"	: 5,
	"offset_encode_mac_pdu"		: 6,
	"offset_mac_pdu_send"			: 7,
	"offset_2nd_bsr_lo_send"		: 8,
	"offset_2nd_bsr_ps_rcv"		: 9
}

keywords_latency = {
	"rlc_pdu"						: "LODATA_DL_RLC_PDU_SEND_REQ::####LATENCY####",
	"bsr_lo_send"					: "send::LOCTRL_DL_BUFFER_STATUS_IND::####LATENCY####",
	"bsr_ps_rcv"					: "eventCallback::LOCTRL_DL_BUFFER_STATUS_IND::####LATENCY####",
	"mux_req_ps_send"				: "sendNewTx::LOCTRL_PDU_MUX_REQ::####LATENCY####",
	"mux_req_lo_rcv"				: "receive::LOCTRL_PDU_MUX_REQ::####LATENCY####",
	"assemble_mac_pdu"			: "ASSEMBLE_MAC_PDU_COMPLETED::####LATENCY####",
	"encode_mac_pdu"				: "sendHarqProcess::####LATENCY####",
	"mac_pdu_send"					: "SEND_MAC_PDU_COMPLETED::####LATENCY####",
	"sec_bsr_lo_send"				: "send::LOCTRL_DL_BUFFER_STATUS_IND::####LATENCY####",
	"sec_bsr_ps_rcv"				: "eventCallback::LOCTRL_DL_BUFFER_STATUS_IND::####LATENCY####"
}

time_string_len = 15

csv_header = ["LOGINFO(filename::line::barabara)",
			  "RLC PDU in lo",
			  "slot trigger rcv in lo",
			  "bsr sent in lo",
			  "bsr rcvd in ps",
			  "mux req sent in ps",
			  "MUX req rcvd in lo",
			  "MAC PDU assemble completed",
			  "encode MAC PDU",
			  "MAC PDU sent in lo",
			  "RLC PDU buffered duration in lo (microsecond)",
			  "bsr flying duration in trans (microsecond)",
			  "MUX req flying duration in trans (microsecond)",
			  "MAC PDU assemble duration in lo (microsecond)",
			  "MAC PDU encode duration in lo (microsecond)",
			  "MAC PDU sent duration (microsecond)",
			  "schedule duration in ps (microsecond)"]

#csv_header = ["LODATA_DL_RLC_PDU_SEND_REQ2LO", "LOCTRL_DL_BUFFER_STATUS_IND2PS", "DELTA_RLC_BSR(microsecond)", "LOCTRL_PDU_MUX_REQ2LO", "DELTA_SCHEDLE(microsecond)", "LO2L1", "DELTA_SEND2L1(microsecond)"]

original_log='journal.txt'
target_csv='latency_result.csv'
latency_to_process='all_latency.txt'
slot_trigger_to_process='slot_trigger.txt'

timestamp_index=8

def write_row_to_csv(file_name, mylist):
	with open(file_name, 'wb') as mycsv:
		wr = csv.writer(mycsv)
		wr.writerows(mylist)

def time_sub_string(time_string):
	max_time_charactor_index = len(time_string) - 1
	tmp_time = time_string[(max_time_charactor_index - time_string_len - 1) : max_time_charactor_index - 1]
	return tmp_time[0:8] + ":" + tmp_time[9:]

def calculate_delta(time_left, time_right):
	# time example hh:mm:ss:xxxxxx -> microsecond
	digit_time_seconds_left = int(time_left[0:2])*3600 + int(time_left[3:5])*60 + int(time_left[6:8])
	digit_time_seconds_right = int(time_right[0:2])*3600 + int(time_right[3:5])*60 + int(time_right[6:8])
	delta_time = 0
	if (digit_time_seconds_right > digit_time_seconds_left):
		delta_time = (digit_time_seconds_right - digit_time_seconds_left) * 1000000 + int(time_right[9:]) - int(time_left[9:])
	elif(digit_time_seconds_right == digit_time_seconds_left):
		delta_time = int(time_right[9:]) - int(time_left[9:])
	else:
		delta_time = (digit_time_seconds_right + 24*3600 - digit_time_seconds_left) * 1000000 + int(time_right[9:]) - int(time_left[9:])

	return str(delta_time)

def in_time_range(low_ts, mid_ts, high_ts):
	digit_low_ts = (int(low_ts[0:2]) * 3600 + int(low_ts[3:5]) * 60 + int(low_ts[6:8])) * 1000000 + int(low_ts[9:])
	digit_mid_ts = (int(mid_ts[0:2]) * 3600 + int(mid_ts[3:5]) * 60 + int(mid_ts[6:8])) * 1000000 + int(mid_ts[9:])
	digit_high_ts = (int(high_ts[0:2]) * 3600 + int(high_ts[3:5]) * 60 + int(high_ts[6:8])) * 1000000 + int(high_ts[9:])

	if (digit_mid_ts > digit_low_ts) and (digit_mid_ts < digit_high_ts):
		return True
	else:
		return False

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

if __name__ == "__main__":
	if len(sys.argv) <= 1:
		print "specify directory"
		sys.exit(0)

	target_dir = sys.argv[1]
	print target_dir

	os.system("grep -nH '####LATENCY####' journal.txt > " + target_dir + "/" + latency_to_process)
	os.system("grep -nH '####SLOTTRIGGERLO####' journal.txt > " + target_dir + "/" + slot_trigger_to_process)

	latency_handle = open(latency_to_process, 'r')
	latency_content = latency_handle.readlines()
	latency_handle.close()

	slot_handle = open(slot_trigger_to_process, 'r')
	slot_content = slot_handle.readlines()
	slot_handle.close()

	csv_record_all = []
	csv_record_all.append(csv_header)

	latency_index = 0
	slot_index = 0

	progress_width = len(latency_content)

	file_number = 1
	for latency_index in range(len(latency_content)):
		# update the bar
		progress(latency_index, progress_width)

		one_example = []

		# 1: rlc pdu keyword
		if keywords_latency["rlc_pdu"] in latency_content[latency_index]:
			rlc_pdu_line = latency_content[latency_index].split()
			# log info
			one_example.append(rlc_pdu_line[0])
			# rlc timestamp
			one_example.append(time_sub_string(rlc_pdu_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index +=1
			continue

		# 2: bsr sent in lo
		if keywords_latency["bsr_lo_send"] in latency_content[latency_index]:
			bsr_lo_send_line = latency_content[latency_index].split()
			# bsr sent timestamp
			one_example.append(time_sub_string(bsr_lo_send_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 3: bsr received in ps
		if keywords_latency["bsr_ps_rcv"] in latency_content[latency_index]:
			bsr_ps_rcv_line = latency_content[latency_index].split()
			# bsr received timestamp
			one_example.append(time_sub_string(bsr_ps_rcv_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 4: mux req sent in ps
		if keywords_latency["mux_req_ps_send"] in latency_content[latency_index]:
			mux_req_ps_send_line = latency_content[latency_index].split()
			# mux req sent timestamp
			one_example.append(time_sub_string(mux_req_ps_send_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 5: mux received in lo
		if keywords_latency["mux_req_lo_rcv"] in latency_content[latency_index]:
			mux_req_lo_rcv_line = latency_content[latency_index].split()
			# mux received timestamp
			one_example.append(time_sub_string(mux_req_lo_rcv_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 6: assemble mac pdu
		if keywords_latency["assemble_mac_pdu"] in latency_content[latency_index]:
			assemble_mac_pdu_line = latency_content[latency_index].split()
			# assemble mac pdu timestamp
			one_example.append(time_sub_string(assemble_mac_pdu_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 7: encode mac pdu
		if keywords_latency["encode_mac_pdu"] in latency_content[latency_index]:
			encode_mac_pdu_line = latency_content[latency_index].split()
			# aencode mac pdu timestamp
			one_example.append(time_sub_string(encode_mac_pdu_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 8: send mac pdu
		if keywords_latency["mac_pdu_send"] in latency_content[latency_index]:
			mac_pdu_send_line = latency_content[latency_index].split()
			# aencode mac pdu timestamp
			one_example.append(time_sub_string(mac_pdu_send_line[timestamp_index]))
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 9: second bsr sent in lo
		if keywords_latency["sec_bsr_lo_send"] in latency_content[latency_index]:
			latency_index += 1
		else:
			latency_index += 1
			continue

		# 10: second bsr received in ps
		if keywords_latency["sec_bsr_ps_rcv"] in latency_content[latency_index]:
			latency_index += 1
		else:
			latency_index += 1
			continue

		# buffer duration in lo
		delta_buffer_duration_in_lo = calculate_delta(one_example[block_offset["offset_rlc_pdu"] + 1], one_example[block_offset["offset_bsr_lo_send"] + 1])
		one_example.append(delta_buffer_duration_in_lo)

		# bsr flying in trans
		bsr_flying_in_trans = calculate_delta(one_example[block_offset["offset_bsr_lo_send"] + 1], one_example[block_offset["offset_bsr_ps_rcv"] + 1])
		one_example.append(bsr_flying_in_trans)

		# mux flying in trans
		mux_flying_in_trans = calculate_delta(one_example[block_offset["offset_mux_req_ps_send"] + 1], one_example[block_offset["offset_mux_req_lo_rcv"] + 1])
		one_example.append(mux_flying_in_trans)

		# save mux request sent timestamp to calculate schedule duration later
		MUX_SEND_IN_PS_TIME_STAMP = one_example[block_offset["offset_mux_req_ps_send"] + 1]

		# assemble mac pdu duration
		assemble_mac_pdu_duration = calculate_delta(one_example[block_offset["offset_mux_req_lo_rcv"] + 1], one_example[block_offset["offset_assemble_mac_pdu"] + 1])
		one_example.append(assemble_mac_pdu_duration)

		# encode mac pdu duration
		encode_mac_pdu_duration = calculate_delta(one_example[block_offset["offset_assemble_mac_pdu"] + 1], one_example[block_offset["offset_encode_mac_pdu"] + 1])
		one_example.append(encode_mac_pdu_duration)

		# send mac pdu duration
		send_mac_pdu_duration = calculate_delta(one_example[block_offset["offset_encode_mac_pdu"] + 1], one_example[block_offset["offset_mac_pdu_send"] + 1])
		one_example.append(send_mac_pdu_duration)

		# slot trigger
		for slot_index in range(len(slot_content)):
			slot_timestamp_line = slot_content[slot_index].split()
			if in_time_range(one_example[block_offset["offset_rlc_pdu"] + 1], time_sub_string(slot_timestamp_line[timestamp_index]), one_example[block_offset["offset_bsr_lo_send"] + 1]):
				real_schedule_slot = slot_content[slot_index + 1].split()
				one_example.insert(2, time_sub_string(real_schedule_slot[timestamp_index]))
				slot_index += 1
				break
			else:
				slot_index += 1

		# schedule duration
		schedule_duration = calculate_delta(one_example[2], MUX_SEND_IN_PS_TIME_STAMP)
		one_example.append(schedule_duration)

		# write to target csv
		csv_record_all.append(one_example)

		# split result if record number over 500
		if len(csv_record_all) > 100:
			write_row_to_csv(target_dir + "/" + "latency_result" + str(file_number) + ".csv", csv_record_all)
			file_number += 1
			del csv_record_all[:]
			csv_record_all.append(csv_header)

	write_row_to_csv(target_dir + "/" + target_csv, csv_record_all)

