for benchmark in alkanes cepdb_subset esol freesolv hopv15 pgp qm8 qm9 sider
do
    fastprop train $benchmark/$benchmark.yml >> $benchmark/run_log.txt 2>&1
done
