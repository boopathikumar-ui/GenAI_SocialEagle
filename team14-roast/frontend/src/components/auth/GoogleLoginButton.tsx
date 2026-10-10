import { Button } from '@chakra-ui/react';
import { GOOGLE_LOGIN_URL } from '../../services/authService';

interface GoogleLoginButtonProps {
  label?: string;
}

export function GoogleLoginButton({ label = 'Continue with Google' }: GoogleLoginButtonProps) {
  const handleClick = (): void => {
    window.location.href = GOOGLE_LOGIN_URL;
  };
  return (
    <Button type="button" variant="outline" rounded="full" w="full" onClick={handleClick}>
      {label}
    </Button>
  );
}

export default GoogleLoginButton;
