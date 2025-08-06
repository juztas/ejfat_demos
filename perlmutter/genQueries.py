
start_time = open("start_time", "r").readline().strip()
end_time = open("end_time", "r").readline().strip()
dp_ipv4 = open("dp_ipv4", "r").readline().strip()
dp_ipv6 = open("dp_ipv6", "r").readline().strip()

Query = f"""
WITH
    toDateTime('{start_time}') AS start_time,
    toDateTime('{end_time}') AS end_time
SELECT
    any(start) as start,
    any(finish) as finish,
    dateDiff('second', start, finish) as duration_s,
    direction,
    esdb_name_src,
    esdb_name_dst,
    sum(packets) AS packets,
    sum(bytes) AS bytes
FROM
(
    SELECT
        start_time as start,
        end_time as finish,
        direction,
        dictGetString('dictionaries.prefix_to_esdb_customer', 'esdb_customer_name', ip_src_bin) AS esdb_name_src,
        ip_src,
        dictGetString('dictionaries.prefix_to_esdb_customer', 'esdb_customer_name', ip_dst_bin) AS esdb_name_dst,
        ip_dst,
        router_name,
        any(sap_routing_instance) AS sap_routing_instance,
        sum(bytes) AS bytes,
        sum(packets) AS packets
    FROM ht.all_flows
    WHERE (export_time_ms > start_time) AND (export_time_ms < end_time) AND  (ip_proto_num = 17) AND 
          (    ( (ip_dst = '{dp_ipv6}') AND (esdb_name_src = 'NERSC') )
           OR  ( (ip_src = '{dp_ipv6}') AND (esdb_name_dst = 'NERSC') )
          )
    GROUP BY
        ip_src,
        ip_src_bin,
        router_name,
        ip_dst,
        ip_dst_bin,
        ip_proto_num,
        direction
)
GROUP BY
    direction,
    esdb_name_src,
    esdb_name_dst
ORDER BY
    direction ASC

"""

print (" ----------- Total Packets in and out of the load balander  ---------------")
print (Query)


