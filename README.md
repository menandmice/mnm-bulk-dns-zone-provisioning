mnm-bulk-dns-zone-provisioning
==============================

This script supports bulk additions and removals of DNS resource
records from a file.

The input file can have two different formats:

Format one for deletions. Each line is a new entry. The first column
is the zonefile, the second column is the DNS domainname (ownername)
to be removed. The first record that is owned by the domainname are removed:

```
84.151.10.in-addr.arpa. 244
84.151.10.in-addr.arpa. 242
84.151.10.in-addr.arpa. 130
21.10.in-addr.arpa. 41.127
21.10.in-addr.arpa. 154.127
21.10.in-addr.arpa. 155.127
21.10.in-addr.arpa. 35.127
```

The second format can be used for deletions and additions. The first
two columns are again the zonename and the ownername. Field three is
the record type, field four is the record data (can be multiple fields
separated by whitespace).

```
84.151.10.in-addr.arpa. 244 PTR www.example.com.
84.151.10.in-addr.arpa. 242 PTR mail.example.net.
84.151.10.in-addr.arpa. 130 PTR ldap.example.org.
example.com. www A 192.0.2.80
example.com. @ NS ns1.example.com.
example.net. @ mx 10 mail.example.com.
```

The column fields are separated by whitespace.

This script requires the Men & Mice Suite CLI mmcmd ( http://www.menandmice.com )

