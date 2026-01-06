import { Button } from '@/components/livekit/button';

function HealthIcon() {
  return (
    <svg
      width="80"
      height="80"
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-6"
    >
      {/* Croix médicale stylisée */}
      <rect x="30" y="10" width="20" height="60" rx="4" fill="#1e3a5f" />
      <rect x="10" y="30" width="60" height="20" rx="4" fill="#1e3a5f" />
      {/* Cœur rouge */}
      <path
        d="M40 58C40 58 54 48 54 38C54 33 50 30 46 30C43 30 41 32 40 34C39 32 37 30 34 30C30 30 26 33 26 38C26 48 40 58 40 58Z"
        fill="#ef4444"
      />
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="px-6">
      <section className="bg-background flex flex-col items-center justify-center text-center">
        <HealthIcon />

        <h1 className="text-[#1e3a5f] text-2xl md:text-3xl font-bold mb-3">
          La santé simplifiée pour tous
        </h1>

        <p className="text-[#1e3a5f] max-w-md text-base md:text-lg leading-7 mb-2">
          Votre assistant santé personnalisé
        </p>

        <p className="text-[#1e3a5f]/70 max-w-lg text-sm md:text-base leading-6 mb-8">
          Un accompagnement par des professionnels de santé, à tous les moments de la vie.
        </p>

        <Button
          variant="primary"
          size="lg"
          onClick={onStartCall}
          className="w-72 font-semibold text-base py-4 bg-[#ef4444] hover:bg-[#dc2626] border-none"
        >
          {startButtonText}
        </Button>

        <p className="text-[#1e3a5f]/50 text-xs mt-6">
          Service disponible 24h/24, 7j/7
        </p>
      </section>
    </div>
  );
};
