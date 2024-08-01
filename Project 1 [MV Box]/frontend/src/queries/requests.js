import { useInfiniteQuery, useMutation, useQuery } from "@tanstack/react-query";
import { endpoints } from "./endpoints";

const callAPI = async (endpoint, params) => {
    const response = await fetch(endpoint, params);
    if (!response.ok) {
        let error = new Error("Fetch error");
        error.response = response;
        error.status = response.status;
        throw error
    }
    return response;
};

export const TopPlaylistsInfiniteQuery = () => {
    const fetchData = async ({ pageParam }) => {
        const payload = new URLSearchParams({
            offset: pageParam,
        });

        const params = {
            method: 'GET',
        };

        const data = (await callAPI(`${endpoints.topPlaylists}?${payload}`, params)).json();
        return data;
    };

    const infiniteQuery = useInfiniteQuery({
        queryKey: ['topPlaylists'],
        queryFn: fetchData,
        initialPageParam: 0,
        getNextPageParam: (lastPage, pages) => lastPage.next_offset,
    });

    return infiniteQuery;
};

export const MVTracksInfiniteQuery = () => {
    const fetchData = async ({ pageParam }) => {
        const payload = new URLSearchParams({
            offset: pageParam,
        });

        const params = {
            method: 'GET',
        };

        const data = (await callAPI(`${endpoints.mvTracks}?${payload}`, params)).json();
        return data;
    };

    const infiniteQuery = useInfiniteQuery({
        queryKey: ['mvTracks'],
        queryFn: fetchData,
        initialPageParam: 0,
        getNextPageParam: (lastPage, pages) => lastPage.next_offset,
    });

    return infiniteQuery;
};

export const TrackPlaylistMutation = () => {
    const mutation = useMutation({
        mutationFn: ({ playlistUrl }) => {
            const params = {
                method: 'POST',
            };
            const payload = new URLSearchParams({
                "playlist_url": playlistUrl,
            });
            return callAPI(`${endpoints.trackPlaylist}?${payload}`, params);
        }
    });

    return mutation;
};

export const MemberJoinMutation = () => {
    const mutation = useMutation({
        mutationFn: ({ name, email, memberType }) => {
            const params = {
                method: 'POST',
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name,
                    email,
                    "member_type": memberType,
                }),
            };
            return callAPI(`${endpoints.memberJoin}`, params);
        }
    });

    return mutation;
};

export const LandingStatsQuery = () => {
    const query = useQuery({
        queryKey: ["landingStats"],
        queryFn: async () => {
            const params = {
                method: 'GET',
            };
            const response = await callAPI(`${endpoints.landingStats}`, params);
            const data = await response.json();
            return data;
        },
    });

    return query;
};