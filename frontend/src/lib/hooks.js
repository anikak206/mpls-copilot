import { useCallback, useEffect, useState } from "react";
import { api, cleanParams, errMsg } from "./api";

export function useList(path, initialFilters = {}, pageSize = 15) {
  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(path, { params: cleanParams({ ...filters, page, page_size: pageSize }) });
      setData(res.data);
      setError("");
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  }, [path, filters, page, pageSize]);

  useEffect(() => {
    load();
  }, [load]);

  const update = (key, value) => {
    setPage(1);
    setFilters((f) => ({ ...f, [key]: value }));
  };

  return { ...data, page, setPage, pageSize, filters, update, loading, error, reload: load };
}

export function useFetch(path, params) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const key = JSON.stringify(params || {});
  const load = useCallback(async () => {
    try {
      const res = await api.get(path, { params: JSON.parse(key) });
      setData(res.data);
      setError("");
    } catch (e) {
      setError(errMsg(e));
    }
  }, [path, key]);
  useEffect(() => {
    load();
  }, [load]);
  return { data, error, reload: load };
}

export function useDevices() {
  const { data } = useFetch("/devices", { page_size: 200 });
  return data?.items || [];
}
