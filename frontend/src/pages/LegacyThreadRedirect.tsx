import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { API_URL } from '../../config';
import { requestJson } from '@/lib/http';
import { ThreadApiResponse } from '@/types/thread';

const LegacyThreadRedirect = () => {
  const navigate = useNavigate();
  const { threadId } = useParams<{ threadId: string }>();

  useEffect(() => {
    if (!threadId) {
      navigate('/', { replace: true });
      return;
    }

    let cancelled = false;

    const resolveCluster = async () => {
      try {
        const thread = await requestJson<ThreadApiResponse>(`${API_URL}/thread/${threadId}`);
        const clusterId = (thread as any)?.cluster_id;
        if (!cancelled) {
          if (clusterId) {
            navigate(`/cluster/${clusterId}/thread/${threadId}`, { replace: true });
          } else {
            toast.error('Thread is not associated with a cluster');
            navigate('/', { replace: true });
          }
        }
      } catch (error) {
        if (!cancelled) {
          toast.error('Thread not found');
          navigate('/', { replace: true });
        }
      }
    };

    resolveCluster();

    return () => {
      cancelled = true;
    };
  }, [threadId, navigate]);

  return (
    <div className="flex h-screen items-center justify-center bg-background text-muted-foreground">
      Redirecting to cluster...
    </div>
  );
};

export default LegacyThreadRedirect;
