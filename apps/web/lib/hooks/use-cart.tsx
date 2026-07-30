"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import * as React from "react";
import { toast } from "sonner";

import { ApiError, api } from "@/lib/api-client";
import type { CartSummary } from "@/lib/types";

import { useAuth } from "./use-auth";

export function useCart() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["cart"],
    queryFn: () => api.get<CartSummary>("/cart"),
    enabled: Boolean(user),
    staleTime: 30_000,
  });

  const invalidate = React.useCallback(
    () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
    [queryClient],
  );

  const add = React.useCallback(
    async (courseId: string) => {
      try {
        await api.post<CartSummary>("/cart", { course_id: courseId });
        await invalidate();
        toast.success("Kurs savatga qo'shildi");
        return true;
      } catch (error) {
        const message =
          error instanceof ApiError ? error.message : "Savatga qo'shib bo'lmadi";
        toast.error(message);
        return false;
      }
    },
    [invalidate],
  );

  const remove = React.useCallback(
    async (courseId: string) => {
      try {
        await api.delete<CartSummary>(`/cart/${courseId}`);
        await invalidate();
        toast.success("Savatdan olib tashlandi");
      } catch (error) {
        toast.error(error instanceof ApiError ? error.message : "Xatolik yuz berdi");
      }
    },
    [invalidate],
  );

  const clear = React.useCallback(async () => {
    await api.delete("/cart");
    await invalidate();
  }, [invalidate]);

  return {
    cart: query.data,
    count: query.data?.items.length ?? 0,
    loading: query.isLoading,
    add,
    remove,
    clear,
    refetch: query.refetch,
  };
}
